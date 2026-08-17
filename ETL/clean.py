"""
Clean stage. This is where the actual data-quality work happens: nulls,
bad types, and the logic contradictions you specifically flagged (like an
Active employee with a past Exit Date).

Every function takes a DataQualityReport and logs what it touched, so
nothing gets silently changed.
"""

import warnings
import numpy as np
import pandas as pd
import config

# pandas warns per-column when it can't infer one consistent date format
# and falls back to per-row parsing with dateutil. Harmless here -- we
# already treat unparseable dates as data-quality issues via errors="coerce"
# -- but on a real 3000-row file with mixed formats it floods the console.
warnings.filterwarnings("ignore", message="Could not infer format")


TODAY = pd.Timestamp.now().normalize()


# ---------------------------------------------------------------------------
# Generic helpers, reused across all four tables
# ---------------------------------------------------------------------------

def trim_strings(df):
    """Strip whitespace on every text column. 'John ' vs 'John' breaks
    joins and dedup silently."""
    obj_cols = df.select_dtypes(include="object").columns
    for c in obj_cols:
        df[c] = df[c].str.strip()
    return df


def parse_dates(df, columns, table, report):
    for col in columns:
        if col not in df.columns:
            continue
        before_valid = df[col].notna().sum()
        df[col] = pd.to_datetime(df[col], errors="coerce")
        after_valid = df[col].notna().sum()
        broken = before_valid - after_valid
        report.log(table, f"unparseable_{col}", broken,
                    f"{col} had a value that wasn't a real date -> set to null")
    return df


def coerce_numeric(df, column, table, report, min_val=None, max_val=None, clip=True):
    if column not in df.columns:
        return df
    original = df[column].copy()
    df[column] = pd.to_numeric(df[column], errors="coerce")
    bad_type_count = ((original.notna()) & (df[column].isna())).sum()
    if bad_type_count > 0:
        report.log(table, f"non_numeric_{column}", bad_type_count,
                    f"{column} contained non-numeric junk -> set to null")

    if min_val is not None or max_val is not None:
        mask = pd.Series(False, index=df.index)
        if min_val is not None:
            mask |= df[column] < min_val
        if max_val is not None:
            mask |= df[column] > max_val
        out_of_range = mask.sum()
        if out_of_range:
            if clip:
                df.loc[mask, column] = df.loc[mask, column].clip(lower=min_val, upper=max_val)
                report.log(table, f"{column}_out_of_range_clipped", out_of_range,
                            f"{column} outside [{min_val}, {max_val}] -> clipped to range")
            else:
                df.loc[mask, column] = np.nan
                report.log(table, f"{column}_out_of_range_nulled", out_of_range,
                            f"{column} outside [{min_val}, {max_val}] -> set to null")
                            
   
    return df

def drop_duplicate_ids(df, id_col, table, report):
    dupe_mask = df.duplicated(subset=[id_col], keep="first")
    n = dupe_mask.sum()
    if n:
        report.log(table, "duplicate_id_dropped", n,
                    f"Duplicate {id_col} kept first occurrence, dropped the rest")
        df = df[~dupe_mask].copy()
    return df


def drop_missing_id(df, id_col, table, report):
    mask = df[id_col].isna() | (df[id_col].astype(str).str.strip() == "")
    n = mask.sum()
    if n:
        report.log(table, "missing_id_dropped", n,
                    f"Rows with no {id_col} can't be linked to anything -> dropped")
        df = df[~mask].copy()
    return df


def drop_orphan_fk(df, fk_col, valid_ids, table, report):
    if fk_col not in df.columns:
        return df
    mask = ~df[fk_col].isin(valid_ids)
    n = mask.sum()
    if n:
        report.log(table, "orphan_fk_dropped", n,
                    f"{fk_col} doesn't match any known employee -> dropped")
        df = df[~mask].copy()
    return df


def title_case(series):
    return series.str.strip().str.title()


def enforce_field_lengths(df, table, report):
    """Last line of defense before load: any text field longer than its
    Postgres VARCHAR width gets nulled and flagged, instead of crashing
    the whole insert (see MAX_FIELD_LENGTHS in config.py)."""
    for column, max_len in config.MAX_FIELD_LENGTHS.get(table, {}).items():
        if column not in df.columns:
            continue
        too_long_mask = df[column].notna() & (df[column].astype(str).str.len() > max_len)
        n = too_long_mask.sum()
        if n:
            df.loc[too_long_mask, column] = np.nan
            report.log(table, f"{column}_malformed_length_cleared", n,
                        f"{column} was longer than {max_len} chars (corrupted source data, not a real value) -> set to null")
    return df


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

def clean_employees(df, report):
    table = "employees"
    df = df.copy()
    df = trim_strings(df)

    # 1. Sensitive / unused columns out, per config
    to_drop = [c for c in config.EMPLOYEE_DROP_COLUMNS if c in df.columns]
    if to_drop:
        df = df.drop(columns=to_drop)
        report.log(table, "columns_dropped", len(to_drop), f"Dropped unused/sensitive columns: {to_drop}")

    # 2. Primary key hygiene
    df = drop_missing_id(df, "employee_id", table, report)
    df = drop_duplicate_ids(df, "employee_id", table, report)

    # 3. Type coercion
    df = parse_dates(df, ["start_date", "exit_date", "dob"], table, report)
    df = coerce_numeric(df, "current_employee_rating", table, report,
                         min_val=config.RATING_RANGE[0], max_val=config.RATING_RANGE[1])
                         
    df["current_employee_rating"] = df["current_employee_rating"].round().astype("Int64")

    # 4. Normalize free-text status into a canonical set
    df["employee_status"] = df["employee_status"].astype(str).str.strip().str.upper().map(
        lambda s: config.CANONICAL_STATUSES.get(s, s.title() if s not in ("NAN", "") else np.nan)
    )
    unknown_status_mask = ~df["employee_status"].isin(config.CANONICAL_STATUSES.values()) & df["employee_status"].notna()
    if unknown_status_mask.any():
        report.log(table, "nonstandard_status_kept", unknown_status_mask.sum(),
                    "employee_status value wasn't in the known set -- kept as-is, title-cased")

    # 5. THE rule you called out: exit_date exists and is already in the
    # past, but the employee is still marked Active. A concrete date is
    # stronger evidence than a status label, so the date wins.
    conflict_mask = (
        (df["employee_status"] == "Active")
        & df["exit_date"].notna()
        & (df["exit_date"] <= TODAY)
    )
    n_conflict = conflict_mask.sum()
    if n_conflict:
        df.loc[conflict_mask, "employee_status"] = "Terminated"
        report.log(table, "active_with_past_exit_date_fixed", n_conflict,
                    "Status said Active but exit_date was already in the past -> status set to Terminated")

    # 6. The mirror problem: exit_date in the future while status is
    # Active is plausible (a resignation notice period) -- don't touch it,
    # but flag it if it's implausibly far out.
    far_future_mask = df["exit_date"] > (TODAY + pd.Timedelta(days=config.FUTURE_EXIT_TOLERANCE_DAYS))
    if far_future_mask.any():
        report.log(table, "implausible_future_exit_date", far_future_mask.sum(),
                    f"exit_date more than {config.FUTURE_EXIT_TOLERANCE_DAYS} days out -- flagged, not changed")

    # 7. Terminated with no exit_date at all -- inconsistent, can't safely
    # invent a date, so just flag it for manual review via a new column.
    df["needs_review"] = False
    missing_exit_mask = (df["employee_status"] == "Terminated") & df["exit_date"].isna()
    df.loc[missing_exit_mask, "needs_review"] = True
    report.log(table, "terminated_missing_exit_date_flagged", missing_exit_mask.sum(),
                "Status is Terminated but exit_date is null -- flagged in needs_review, not guessed")

    # 8. exit_date before start_date is impossible
    bad_order_mask = df["exit_date"].notna() & df["start_date"].notna() & (df["exit_date"] < df["start_date"])
    if bad_order_mask.any():
        df.loc[bad_order_mask, "exit_date"] = pd.NaT
        df.loc[bad_order_mask, "needs_review"] = True
        report.log(table, "exit_before_start_cleared", bad_order_mask.sum(),
                    "exit_date was before start_date -- impossible, exit_date nulled and flagged")

    # 9. start_date in the future is impossible for a real employee record
    future_start_mask = df["start_date"] > TODAY
    if future_start_mask.any():
        df.loc[future_start_mask, "needs_review"] = True
        report.log(table, "future_start_date_flagged", future_start_mask.sum(),
                    "start_date is in the future -- flagged for review")

    # 10. DOB sanity: in the future, or employee younger than working age /
    # older than plausible at hire time
    dob_future_mask = df["dob"] > TODAY
    if dob_future_mask.any():
        df.loc[dob_future_mask, "dob"] = pd.NaT
        report.log(table, "dob_in_future_nulled", dob_future_mask.sum(),
                    "dob was in the future -- impossible, set to null")

    age_at_hire = (df["start_date"] - df["dob"]).dt.days / 365.25
    underage_mask = age_at_hire.notna() & (age_at_hire < config.MIN_WORKING_AGE)
    if underage_mask.any():
        df.loc[underage_mask, "needs_review"] = True
        report.log(table, "underage_at_hire_flagged", underage_mask.sum(),
                    f"Employee was under {config.MIN_WORKING_AGE} at start_date -- flagged, dob/start_date not guessed")

    # 11. Missing critical text fields -> explicit "Unknown" bucket instead
    # of null (keeps downstream grouping/joins from silently dropping rows)
    for col, label in [("business_unit", "Unknown Business Unit"),
                        ("department_type", "Unknown Department"),
                        ("title", "Unknown Title")]:
        if col in df.columns:
            n_missing = df[col].isna().sum()
            if n_missing:
                df[col] = df[col].fillna(label)
                report.log(table, f"{col}_filled_unknown", n_missing,
                            f"Missing {col} filled with '{label}' so grouping/joins don't drop rows")

    if "division_description" in df.columns:
        df["division_description"] = df["division_description"].fillna("Unknown Division")

    # 12. Name casing, gender normalization
    df["first_name"] = title_case(df["first_name"].astype(str))
    df["last_name"] = title_case(df["last_name"].astype(str))
    if "gender" in df.columns:
        df["gender"] = df["gender"].astype(str).str.strip().str.upper().replace({"NAN": np.nan})

    # 13. Email: normalize, validate, synthesize a placeholder if missing
    # (we need *some* unique login email downstream for the users table)
    email_valid = df["email"].astype(str).str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", na=False)
    bad_email_mask = df["email"].notna() & ~email_valid
    n_bad_email = bad_email_mask.sum()
    df.loc[bad_email_mask, "email"] = np.nan
    if n_bad_email:
        report.log(table, "invalid_email_cleared", n_bad_email,
                    "email didn't look like a real address -- cleared, will be synthesized")

    missing_email_mask = df["email"].isna()
    n_missing_email = missing_email_mask.sum()

    # lowercase every already-valid email up front, regardless of whether
    # any rows below need synthesis -- otherwise "John@x.com" and
    # "john@x.com" look like different emails and dedup misses them
    df.loc[~missing_email_mask, "email"] = df.loc[~missing_email_mask, "email"].str.lower()

    if n_missing_email:
        synth = (
            df.loc[missing_email_mask, "first_name"].str.lower()
            + "."
            + df.loc[missing_email_mask, "last_name"].str.lower()
            + "."
            + df.loc[missing_email_mask, "employee_id"].astype(str)
            + "@smarterp.local"
        )
        df.loc[missing_email_mask, "email"] = synth
        report.log(table, "email_synthesized", n_missing_email,
                    "email was missing/invalid -- synthesized a placeholder (name.id@smarterp.local)")

    # duplicate emails after cleaning would break a UNIQUE constraint on users.email
    dupe_email_mask = df.duplicated(subset=["email"], keep="first")
    if dupe_email_mask.any():
        idx = df.index[dupe_email_mask]
        df.loc[idx, "email"] = [
            f"{e.split('@', 1)[0]}+{eid}@{e.split('@', 1)[1]}" if isinstance(e, str) and "@" in e else e
            for e, eid in zip(df.loc[idx, "email"], df.loc[idx, "employee_id"])
        ]
        report.log(table, "duplicate_email_deduplicated", len(idx),
                    "Two employees ended up with the same email -- made unique with a +employee_id tag")

    df = enforce_field_lengths(df, table, report)

    print(f"  employees cleaned: {len(df)} rows kept, {df['needs_review'].sum()} flagged for manual review")
    # 14. Sanitize self-referencing manager_id
    if "manager_id" in df.columns:
        # Convert to nullable integer to fix the '3910.0' float issue
        df["manager_id"] = pd.to_numeric(df["manager_id"], errors="coerce").astype("Int64")
        
        # Find manager IDs that do not exist in the employee_id column
        valid_employee_ids = set(df["employee_id"])
        invalid_manager_mask = df["manager_id"].notna() & ~df["manager_id"].isin(valid_employee_ids)
        
        n_invalid = invalid_manager_mask.sum()
        if n_invalid:
            # Set orphan manager_ids to null (pd.NA) so Postgres accepts them
            df.loc[invalid_manager_mask, "manager_id"] = pd.NA
            
            # Log it in the report if you are in clean.py
            if "report" in locals():
                report.log(table, "orphan_manager_id_nulled", n_invalid, 
                           "manager_id did not match any known employee_id -> set to null")
    return df


# ---------------------------------------------------------------------------
# Trainings
# ---------------------------------------------------------------------------

def clean_trainings(df, valid_employee_ids, report):
    table = "trainings"
    df = df.copy()
    df = trim_strings(df)

    df = drop_orphan_fk(df, "employee_id", valid_employee_ids, table, report)
    df = parse_dates(df, ["training_date"], table, report)

    future_mask = df["training_date"] > TODAY
    if future_mask.any():
        report.log(table, "future_training_date_flagged", future_mask.sum(),
                    "training_date is in the future -- kept (could be scheduled), just flagged")

    df = coerce_numeric(df, "training_duration_days", table, report, min_val=0, max_val=None)
    df = coerce_numeric(df, "training_cost", table, report, min_val=0, max_val=None)
    df["training_duration_days"] = df["training_duration_days"].fillna(0)
    df["training_cost"] = df["training_cost"].fillna(0)

    if "training_outcome" in df.columns:
        df["training_outcome"] = df["training_outcome"].fillna("Unknown")
    if "training_type" in df.columns:
        df["training_type"] = df["training_type"].fillna("Unknown")

    df = enforce_field_lengths(df, table, report)

    print(f"  trainings cleaned: {len(df)} rows kept")
    return df


# ---------------------------------------------------------------------------
# Recruitment
# ---------------------------------------------------------------------------

def clean_recruitment(df, report):
    table = "recruitment"
    df = df.copy()
    df = trim_strings(df)

    df = drop_missing_id(df, "applicant_id", table, report)
    df = drop_duplicate_ids(df, "applicant_id", table, report)

    df = parse_dates(df, ["application_date", "dob"], table, report)
    df["first_name"] = title_case(df["first_name"].astype(str))
    df["last_name"] = title_case(df["last_name"].astype(str))

    if "status" in df.columns:
        df["status"] = df["status"].fillna("Unknown").str.strip().str.upper()

    df = coerce_numeric(df, "years_of_experience", table, report, min_val=0, max_val=config.MAX_YEARS_EXPERIENCE)
    df = coerce_numeric(df, "desired_salary", table, report, min_val=0, max_val=None)

    dob_future_mask = df["dob"] > TODAY
    if dob_future_mask.any():
        df.loc[dob_future_mask, "dob"] = pd.NaT
        report.log(table, "dob_in_future_nulled", dob_future_mask.sum(),
                    "dob was in the future -- set to null")

    app_future_mask = df["application_date"] > TODAY
    if app_future_mask.any():
        df.loc[app_future_mask, "application_date"] = pd.NaT
        report.log(table, "application_date_in_future_nulled", app_future_mask.sum(),
                    "application_date was in the future -- set to null")

    df = enforce_field_lengths(df, table, report)

    print(f"  recruitment cleaned: {len(df)} rows kept")
    return df


# ---------------------------------------------------------------------------
# Surveys
# ---------------------------------------------------------------------------

def clean_surveys(df, valid_employee_ids, report):
    table = "surveys"
    df = df.copy()
    df = trim_strings(df)

    df = drop_orphan_fk(df, "employee_id", valid_employee_ids, table, report)
    df = parse_dates(df, ["survey_date"], table, report)

    lo, hi = config.SURVEY_SCORE_RANGE
    for col in ["engagement_score", "satisfaction_score", "work_life_balance_score"]:
        df = coerce_numeric(df, col, table, report, min_val=lo, max_val=hi)

    df = enforce_field_lengths(df, table, report)

    print(f"  surveys cleaned: {len(df)} rows kept")
    return df
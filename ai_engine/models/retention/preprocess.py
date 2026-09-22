import pandas as pd
from sqlalchemy import text
from database import engine
import config


def fetch_raw_data(only_active=False):
    """STEP 1A: Extract raw data from PostgreSQL."""
    where_clause = "WHERE is_deleted = FALSE"
    if only_active:
        where_clause += " AND UPPER(employee_status) IN ('ACTIVE', 'ON LEAVE')"

    query = f"SELECT * FROM v_ai_retention_features {where_clause};"
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def is_churned(status_series, churn_statuses=None):
    """Whether each employee_status counts as 'left the company'.

    Uses substring matching so "Terminated" also catches "Voluntarily
    Terminated" and "Terminated For Cause", mirroring how the SQL views
    (v_department_turnover, v_attrition_risk_indicators, etc.) define churn.
    """
    churn_statuses = churn_statuses or config.CHURN_STATUSES
    pattern = "|".join(s.upper() for s in churn_statuses)
    return status_series.fillna("").str.upper().str.contains(pattern, regex=True)


def normalize_gender(df):
    """Collapses inconsistent casing ("Male" vs "MALE") into one category
    per real value, instead of letting them silently become two."""
    df = df.copy()
    if "gender" in df.columns:
        df["gender"] = df["gender"].fillna("Unknown").astype(str).str.strip().str.upper()
    return df


def bucket_rare_categories(df, columns, min_count=None, other_label="Other", mapping=None):
    """Collapses categories with fewer than `min_count` rows into `other_label`.

    Pass `mapping` (a dict of {column: set(values_to_keep)}) to apply a mapping
    computed earlier (e.g. at training time) rather than recomputing thresholds
    from this df -- required at prediction time so the same categories are
    treated as "Other" as during training, even if this batch's counts differ.

    Returns (bucketed_df, mapping) so callers can save the mapping for reuse.
    """
    min_count = min_count if min_count is not None else config.MIN_CATEGORY_COUNT
    df = df.copy()
    out_mapping = {}

    for col in columns:
        if col not in df.columns:
            continue
        series = df[col].fillna("Unknown").astype(str)

        if mapping is not None and col in mapping:
            keep = mapping[col]
        else:
            counts = series.value_counts()
            keep = set(counts[counts >= min_count].index)

        out_mapping[col] = keep
        df[col] = series.where(series.isin(keep), other_label)

    return df, out_mapping


def _unique_categories(series):
    """Sorted unique text values, always including 'Unknown' exactly once.
    (fillna('Unknown') can already produce 'Unknown', so a plain
    `+ ['Unknown']` would create a duplicate category and crash pandas.)"""
    values = set(series.fillna("Unknown").astype(str).unique().tolist())
    values.add("Unknown")
    return sorted(values)


def clean_raw_data(df, category_mapping=None):
    """Single entry point for all pre-treatment that must be IDENTICAL between
    training and prediction: gender normalization + rare-category bucketing.

    At training time, call with category_mapping=None; it computes the
    mapping from this data and returns it so it can be saved alongside the
    model. At prediction time, pass the saved mapping so new/unseen data is
    bucketed the same way training data was.
    """
    df = normalize_gender(df)
    df, mapping = bucket_rare_categories(
        df,
        columns=["division_description", "job_function"],
        mapping=category_mapping,
    )
    return df, mapping


def capture_text_categories(df):
    """STEP 1B: Create a dictionary of all text categories (e.g., Departments).
    This ensures the model knows all possible text values during training."""
    return {col: _unique_categories(df[col]) for col in config.CATEGORICAL_FEATURES}


def format_ml_features(df, schema=None):
    """STEP 1C: Clean and format the data (Pre-treatment)."""
    df = df.copy()

    # 1. Convert start dates to numerical 'tenure_days'
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["tenure_days"] = (pd.Timestamp.now().normalize() - df["start_date"]).dt.days

    # 2. Format text columns based on the schema
    for col in config.CATEGORICAL_FEATURES:
        df[col] = df[col].fillna("Unknown").astype(str)
        categories = schema[col] if schema else _unique_categories(df[col])
        df[col] = pd.Categorical(df[col], categories=categories)

    # 3. Combine Categorical (text) and Numeric features
    all_features = config.CATEGORICAL_FEATURES + config.NUMERIC_FEATURES

    # Return ONLY the columns the ML model needs to learn from
    return df[all_features]
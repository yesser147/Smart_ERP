"""
Extract stage. Gets the 4 raw Kaggle CSVs into memory safely -- no
cleaning happens here, that's clean.py's job.

Column matching is alias-based and normalization-tolerant (case, spaces,
punctuation all ignored) because Kaggle mirrors of this dataset use
different header conventions ("Employee ID" vs "EmpID"). See the
*_ALIASES dicts in config.py. If a canonical column truly can't be found,
it's created empty with a warning instead of crashing downstream.
"""

import os
import re
import pandas as pd
import config


def _normalize(s):
    """Case/space/punctuation-insensitive key for matching header names."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _read_csv_safely(path):
    """Kaggle exports are usually utf-8, but fall back to latin-1 so a bad
    encoding doesn't crash the whole pipeline."""
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        print(f"  utf-8 failed for {os.path.basename(path)}, retrying with latin-1")
        df = pd.read_csv(path, encoding="latin-1")

    # strip whitespace from header names -- "Employee ID " vs "Employee ID"
    # is a classic silent bug
    df.columns = [c.strip() for c in df.columns]
    return df


def _resolve_columns(df, aliases, table_name):
    """Renames df's columns to canonical names using the alias lists,
    matched normalization-insensitively. Guarantees every canonical column
    exists afterward (filled with empty values if genuinely not found)."""
    normalized_actual = {_normalize(c): c for c in df.columns}

    rename_map = {}
    missing = []
    for canonical, variants in aliases.items():
        match = next((normalized_actual[_normalize(v)] for v in variants
                      if _normalize(v) in normalized_actual), None)
        if match:
            rename_map[match] = canonical
        else:
            missing.append(canonical)

    df = df.rename(columns=rename_map)

    for canonical in missing:
        df[canonical] = pd.NA

    if missing:
        print(f"  WARNING: {table_name} -- couldn't find a column for {missing}; "
              f"filled with empty values. If your file really has this data, "
              f"add its exact header text to the matching alias list in config.py.")

    return df


def _load_one(key, filename, aliases):
    path = os.path.join(config.INPUT_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Expected '{filename}' in {config.INPUT_DIR} but it's not there. "
            f"Set ETL_INPUT_DIR or drop the Kaggle CSVs in that folder."
        )
    df = _read_csv_safely(path)
    df = _resolve_columns(df, aliases, key)
    print(f"  loaded {key}: {len(df)} rows, {len(df.columns)} columns")
    return df


def extract_all():
    """Returns a dict of raw dataframes, columns already renamed to the
    canonical snake_case names used everywhere downstream."""
    print("EXTRACT")
    raw = {
        "employees": _load_one("employees", config.RAW_FILES["employees"], config.EMPLOYEE_ALIASES),
        "trainings": _load_one("trainings", config.RAW_FILES["trainings"], config.TRAINING_ALIASES),
        "recruitment": _load_one("recruitment", config.RAW_FILES["recruitment"], config.RECRUITMENT_ALIASES),
        "surveys": _load_one("surveys", config.RAW_FILES["surveys"], config.SURVEY_ALIASES),
    }
    return raw
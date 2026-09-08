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

    BUG FIXED HERE: every one of your SQL views (v_department_turnover,
    v_attrition_risk_indicators, etc.) matches termination with
    `UPPER(employee_status) LIKE '%TERMINATED%'` -- catching any casing
    and any suffix like 'Terminated - Voluntary'. The old label logic in
    train_model() used a strict `.isin(["Terminated"])`, which misses
    every one of those variants your own dashboard already counts as
    churn. That's not a crash -- it silently mislabels real churners as
    "stayed", corrupting the ground truth the whole model learns from.
    This mirrors the SQL views' logic exactly instead of duplicating a
    different, stricter definition in Python.
    """
    churn_statuses = churn_statuses or config.CHURN_STATUSES
    pattern = "|".join(s.upper() for s in churn_statuses)
    return status_series.fillna("").str.upper().str.contains(pattern, regex=True)


def capture_text_categories(df):
    """STEP 1B: Create a dictionary of all text categories (e.g., Departments).
    This ensures the model knows all possible text values during training."""
    return {
        col: sorted(df[col].fillna("Unknown").astype(str).unique().tolist() + ["Unknown"])
        for col in config.CATEGORICAL_FEATURES
    }


def format_ml_features(df, schema=None):
    """STEP 1C: Clean and format the data (Pre-treatment)."""
    df = df.copy()

    # 1. Convert start dates to numerical 'tenure_days'
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["tenure_days"] = (pd.Timestamp.now().normalize() - df["start_date"]).dt.days

    # 2. Format text columns based on the schema
    for col in config.CATEGORICAL_FEATURES:
        df[col] = df[col].fillna("Unknown").astype(str)
        categories = schema[col] if schema else sorted(df[col].unique().tolist() + ["Unknown"])
        df[col] = pd.Categorical(df[col], categories=categories)

    # 3. Combine Categorical (text) and Numeric features
    all_features = config.CATEGORICAL_FEATURES + config.NUMERIC_FEATURES

    # Return ONLY the columns the ML model needs to learn from
    return df[all_features]
import pandas as pd
from sqlalchemy import text
from database import engine
import config

def fetch_raw(only_active=False):
    """Pulls data from the Postgres database view."""
    where_clause = "WHERE is_deleted = FALSE"
    if only_active:
        where_clause += " AND employee_status = 'Active'"

    query = f"SELECT * FROM v_ai_retention_features {where_clause};"
    
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def build_features(df, schema=None):
    """Turns raw DB rows into an XGBoost-ready feature matrix."""
    df = df.copy()

    # Calculate tenure in days from start_date
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["tenure_days"] = (pd.Timestamp.now().normalize() - df["start_date"]).dt.days

    # Lock categorical feature types to schema
    for col in config.CATEGORICAL_FEATURES:
        df[col] = df[col].fillna("Unknown").astype(str)
        categories = schema[col] if schema else sorted(df[col].unique().tolist() + ["Unknown"])
        df[col] = pd.Categorical(df[col], categories=categories)

    feature_cols = config.CATEGORICAL_FEATURES + config.NUMERIC_FEATURES
    return df[feature_cols]


def get_category_schema(df):
    """Captures categorical schema at training time to lock feature dimensions."""
    return {
        col: sorted(df[col].fillna("Unknown").astype(str).unique().tolist() + ["Unknown"])
        for col in config.CATEGORICAL_FEATURES
    }
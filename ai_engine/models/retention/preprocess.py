import pandas as pd
from sqlalchemy import text
from database import engine
import config

def fetch_raw_data(only_active=False):
    """STEP 1A: Extract raw data from PostgreSQL."""
    where_clause = "WHERE is_deleted = FALSE"
    if only_active:
        where_clause += " AND employee_status = 'Active'"

    query = f"SELECT * FROM v_ai_retention_features {where_clause};"
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

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
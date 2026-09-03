import os
import joblib
import pandas as pd
import xgboost as xgb
from database import engine

FEATURES = ['training_budget', 'headcount', 'avg_engagement', 'department_turnover_rate']
TARGET = 'avg_performance'

def train_budget_model():
    """Trains an XGBoost Regressor to predict performance rating based on training spend."""
    print("Fetching training budget features from database...")
    query = "SELECT * FROM v_ai_training_budget_features;"
    df = pd.read_sql(query, engine).fillna(0)
    
    if df.empty or len(df) < 2:
        print("Warning: Insufficient department data to train regression model.")
        return

    X = df[FEATURES]
    y = df[TARGET]

    print("Training XGBoost Regressor for budget elasticity...")
    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=3,
        random_state=42
    )
    model.fit(X, y)

    os.makedirs('models/budget/saved_models', exist_ok=True)
    joblib.dump(model, 'models/budget/saved_models/budget_xgboost.pkl')
    print("Model saved to models/budget/saved_models/budget_xgboost.pkl")

if __name__ == "__main__":
    train_budget_model()
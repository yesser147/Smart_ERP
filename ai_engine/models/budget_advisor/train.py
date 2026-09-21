import os
import json
import joblib
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import RepeatedKFold, cross_val_score
from database import engine

FEATURES = ['training_budget', 'headcount', 'avg_engagement', 'department_turnover_rate']
TARGET = 'avg_performance'
MIN_HEADCOUNT = 3   # smaller departments: an average over 1-2 people is noise
MIN_ROWS = 20

MODEL_PATH = 'models/budget/saved_models/budget_xgboost.pkl'
METRICS_PATH = 'models/budget/saved_models/budget_metrics.json'


def train_budget_model():
    """Trains an XGBoost Regressor to predict performance from training spend,
    and saves honest quality metrics next to the model."""
    print("Fetching training budget features from database...")
    df = pd.read_sql("SELECT * FROM v_ai_training_budget_features;", engine)
    n_total = len(df)

    # Only departments with a real, meaningful performance average
    df = df.dropna(subset=[TARGET])
    df = df[df['headcount'] >= MIN_HEADCOUNT].copy()
    # Same preparation as the prescriptor
    df[FEATURES] = df[FEATURES].fillna(df[FEATURES].median())

    print(f"Departments in view: {n_total}, usable (headcount >= {MIN_HEADCOUNT}): {len(df)}")
    if len(df) < MIN_ROWS:
        print(f"Not enough usable departments (need {MIN_ROWS}). Lower MIN_HEADCOUNT or check the data.")
        return

    X = df[FEATURES]
    y = df[TARGET]
    print(f"Budget range in data: {X['training_budget'].min():.0f} to {X['training_budget'].max():.0f}")

    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=2,
        min_child_weight=5,
        random_state=42
    )

    cv = RepeatedKFold(n_splits=5, n_repeats=3, random_state=42)
    r2 = cross_val_score(model, X, y, cv=cv, scoring='r2')
    mae = -cross_val_score(model, X, y, cv=cv, scoring='neg_mean_absolute_error')
    print(f"CV R2: {r2.mean():.3f} (+/- {r2.std():.3f})")
    print(f"CV MAE: {mae.mean():.3f}")

    print("Training final model on all usable data...")
    model.fit(X, y)

    os.makedirs('models/budget/saved_models', exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metrics = {
        "n_rows": int(len(df)),
        "n_rows_total": int(n_total),
        "min_headcount": MIN_HEADCOUNT,
        "budget_min": float(X['training_budget'].min()),
        "budget_max": float(X['training_budget'].max()),
        "target_std": round(float(y.std()), 3),
        "cv_r2": round(float(r2.mean()), 3),
        "cv_r2_std": round(float(r2.std()), 3),
        "cv_mae": round(float(mae.mean()), 3),
    }
    with open(METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Metrics saved to {METRICS_PATH}")


if __name__ == "__main__":
    train_budget_model()
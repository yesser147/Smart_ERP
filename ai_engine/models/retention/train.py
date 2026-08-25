"""
Trains the flight-risk XGBoost classifier and saves it to artifacts/.

Run it standalone:
    python -m models.retention.train

Re-run this periodically (e.g. monthly, or after a big ETL refresh) to
keep the model current -- it always trains from whatever's in Postgres
right now, so results will drift as more employees leave and the
dataset grows past this initial synthetic seed.
"""

import os
import joblib
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

import config
from models.retention.features import fetch_raw, build_features, get_category_schema


def train():
    print("Pulling training data (all employees, active + terminated)...")
    raw = fetch_raw(only_active=False)
    print(f"  {len(raw)} employees pulled")

    if raw["employee_status"].isin(config.CHURN_STATUSES).sum() < 10:
        print("WARNING: fewer than 10 terminated employees in the data. "
              "XGBoost needs real examples of churn to learn from -- "
              "results will be unreliable until there's more history.")

    schema = get_category_schema(
        raw[config.CATEGORICAL_FEATURES].astype(str)
    )
    X = build_features(raw, schema=schema)
    y = raw["employee_status"].isin(config.CHURN_STATUSES).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        enable_categorical=True,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    print("\n--- Evaluation on held-out test set ---")
    print(classification_report(y_test, preds, target_names=["Stayed", "Left"]))
    if len(np.unique(y_test)) > 1:
        print(f"ROC AUC: {roc_auc_score(y_test, probs):.3f}")
    else:
        print("ROC AUC: skipped (test split ended up with only one class -- "
              "normal on small/imbalanced datasets, not a bug)")

    os.makedirs(config.ARTIFACT_DIR, exist_ok=True)
    model.save_model(config.RETENTION_MODEL_PATH)
    joblib.dump({"category_schema": schema, "feature_cols": list(X.columns)},
                config.RETENTION_SCHEMA_PATH)
    print(f"\nSaved model -> {config.RETENTION_MODEL_PATH}")
    print(f"Saved feature schema -> {config.RETENTION_SCHEMA_PATH}")


if __name__ == "__main__":
    train()
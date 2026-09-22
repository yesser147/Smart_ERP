import os
import json
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report

import config
from models.retention import preprocess as prep

METRICS_PATH = os.path.join(config.ARTIFACT_DIR, "retention_metrics.json")


def make_model():
    return xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        enable_categorical=True,  # Tells XGBoost to accept our text categories
        eval_metric="logloss",
        random_state=42,
    )


def train_model():
    print("1. Fetching all historical data (Active + Terminated)...")
    raw_df = prep.fetch_raw_data(only_active=False)

    print("1b. Cleaning: normalizing gender, bucketing rare categories...")
    raw_df, category_mapping = prep.clean_raw_data(raw_df)
    for col, keep in category_mapping.items():
        print(f"    {col}: kept {len(keep)} categories (>= {config.MIN_CATEGORY_COUNT} rows), rest -> 'Other'")

    print("2. Pre-treating data...")
    schema = prep.capture_text_categories(raw_df)
    X = prep.format_ml_features(raw_df, schema=schema)  # The Features (inputs)
    y = prep.is_churned(raw_df["employee_status"]).astype(int)  # The Target (1 for quit, 0 for stayed)

    n_churned = int(y.sum())
    if n_churned < 10:
        print(f"WARNING: only {n_churned} churned employees found in the data. "
              f"XGBoost needs real examples to learn from -- results will be "
              f"unreliable until there's more termination history.")

    print("3. Splitting data into Training (80%) and Validation (20%) sectors...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("4. Training the XGBoost Model on the training split...")
    model = make_model()
    model.fit(X_train, y_train)

    print("5. Validating model on unseen data...")
    predictions = model.predict(X_test)
    print("\nValidation Report:")
    print(classification_report(y_test, predictions, target_names=["Stayed", "Left"]))

    print("6. Cross-validated quality (5-fold, each employee scored by a model that never saw them)...")
    cv_auc = cv_auc_std = cv_pr = None
    if min(n_churned, len(y) - n_churned) >= 20:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        auc = cross_val_score(make_model(), X, y, cv=cv, scoring="roc_auc")
        pr = cross_val_score(make_model(), X, y, cv=cv, scoring="average_precision")
        cv_auc, cv_auc_std, cv_pr = float(auc.mean()), float(auc.std()), float(pr.mean())
        print(f"CV AUC: {cv_auc:.3f} (+/- {cv_auc_std:.3f})  [0.50 = pure chance]")
        print(f"CV PR-AUC: {cv_pr:.3f}  [base churn rate: {y.mean():.3f}]")
    else:
        print("Not enough examples of one class for cross-validation.")

    print("7. Training the final model on all data and saving artifacts...")
    final_model = make_model()
    final_model.fit(X, y)

    os.makedirs(config.ARTIFACT_DIR, exist_ok=True)
    final_model.save_model(config.RETENTION_MODEL_PATH)
    joblib.dump(
        {
            "category_schema": schema,
            "feature_cols": list(X.columns),
            "category_mapping": category_mapping,  # needed by predict.py to bucket the same way
        },
        config.RETENTION_SCHEMA_PATH,
    )

    metrics = {
        "n_rows": int(len(y)),
        "n_churned": n_churned,
        "churn_rate": round(float(y.mean()), 3),
        "features": list(X.columns),
        "cv_auc": None if cv_auc is None else round(cv_auc, 3),
        "cv_auc_std": None if cv_auc_std is None else round(cv_auc_std, 3),
        "cv_pr_auc": None if cv_pr is None else round(cv_pr, 3),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {METRICS_PATH}")
    print("Done!")


if __name__ == "__main__":
    train_model()
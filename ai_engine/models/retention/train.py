import os
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

import config
from models.retention import preprocess as prep

def train_model():
    print("1. Fetching all historical data (Active + Terminated)...")
    raw_df = prep.fetch_raw_data(only_active=False)

    print("2. Pre-treating data...")
    schema = prep.capture_text_categories(raw_df)
    X = prep.format_ml_features(raw_df, schema=schema) # The Features (inputs)
    y = raw_df["employee_status"].isin(config.CHURN_STATUSES).astype(int) # The Target (1 for quit, 0 for stayed)

    print("3. Splitting data into Training (80%) and Validation (20%) sectors...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("4. Training the XGBoost Model...")
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        enable_categorical=True, # Tells XGBoost to accept our text categories
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    print("5. Validating model on unseen data...")
    predictions = model.predict(X_test)
    print("\nValidation Report:")
    print(classification_report(y_test, predictions, target_names=["Stayed", "Left"]))

    print("6. Saving artifacts for future predictions...")
    os.makedirs(config.ARTIFACT_DIR, exist_ok=True)
    model.save_model(config.RETENTION_MODEL_PATH)
    joblib.dump({"category_schema": schema, "feature_cols": list(X.columns)}, config.RETENTION_SCHEMA_PATH)
    print("Done!")

if __name__ == "__main__":
    train_model()
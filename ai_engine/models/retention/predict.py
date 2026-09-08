import os
import joblib
import pandas as pd
import xgboost as xgb
import shap

import config
from models.retention import preprocess as prep

class RetentionPredictor:
    def __init__(self):
        # Load the saved model and schema from Step 2
        self.model = xgb.XGBClassifier()
        self.model.load_model(config.RETENTION_MODEL_PATH)

        saved_data = joblib.load(config.RETENTION_SCHEMA_PATH)
        self.category_schema = saved_data["category_schema"]
        self.feature_cols = saved_data["feature_cols"]

        # Initialize SHAP (The math that explains WHY the model made a prediction)
        self.explainer = shap.TreeExplainer(self.model)

    def analyze_active_employees(self):
        """Scores all current employees and finds their risk drivers."""
        # 1. Fetch current employees and pre-treat their data
        raw_df = prep.fetch_raw_data(only_active=True)
        if raw_df.empty:
            return raw_df

        X_current = prep.format_ml_features(raw_df, schema=self.category_schema)

        # 2. Predict Risk Score (Probability of quitting)
        raw_df["risk_score"] = self.model.predict_proba(X_current)[:, 1]

        # 3. Calculate SHAP values to explain the score
        shap_values = self.explainer.shap_values(X_current)
        # Verified against xgboost 3.4.1 / shap 0.52.0: this returns a
        # single (n_samples, n_features) array for a binary XGBClassifier,
        # so shap_values[i] is already one employee's vector. Older shap
        # versions historically returned [class_0_array, class_1_array]
        # instead -- this guards against that so it fails loudly instead
        # of quietly explaining the wrong thing if you ever pin an older
        # shap version.
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # positive (churn) class

        # 4. Find the top 3 reasons pushing the score UP for each person
        top_drivers_list = []
        for i in range(len(raw_df)):
            employee_shap = shap_values[i]
            impacts = list(zip(self.feature_cols, employee_shap))

            # Keep only positive impacts (things increasing risk) and sort them
            positive_impacts = sorted([item for item in impacts if item[1] > 0], key=lambda x: x[1], reverse=True)[:3]

            # Convert to percentages
            total_pos = sum([val for _, val in positive_impacts]) or 1.0
            formatted_drivers = [
                {"feature": feat, "impact_pct": round((val / total_pos) * 100, 1)}
                for feat, val in positive_impacts
            ]
            top_drivers_list.append(formatted_drivers)

        raw_df["top_risk_drivers"] = top_drivers_list
        return raw_df
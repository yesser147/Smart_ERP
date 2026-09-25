import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import shap

import config
from models.retention import preprocess as prep
from models.retention.train import fold_model_path

class RetentionPredictor:
    def __init__(self):
        # Final model (all data): used for employees the training never saw
        self.model = xgb.XGBClassifier()
        self.model.load_model(config.RETENTION_MODEL_PATH)

        saved_data = joblib.load(config.RETENTION_SCHEMA_PATH)
        self.category_schema = saved_data["category_schema"]
        self.feature_cols = saved_data["feature_cols"]
        self.category_mapping = saved_data.get("category_mapping", {})

        # Out-of-fold models: an employee who was in the training data is
        # scored by the fold model that did NOT see them (otherwise the model
        # just remembers that current employees stayed).
        self.fold_of = saved_data.get("fold_of_employee", {})
        self.fold_models = []
        for k in range(saved_data.get("n_folds", 0)):
            path = fold_model_path(k)
            if os.path.exists(path):
                m = xgb.XGBClassifier()
                m.load_model(path)
                self.fold_models.append(m)
        if len(self.fold_models) != saved_data.get("n_folds", 0):
            self.fold_models, self.fold_of = [], {}   # incomplete artifacts: use the final model

    def analyze_active_employees(self):
        """Scores all current employees and finds their risk drivers."""
        # 1. Fetch current employees and pre-treat them exactly like train.py
        raw_df = prep.fetch_raw_data(only_active=True)
        if raw_df.empty:
            return raw_df
        raw_df, _ = prep.clean_raw_data(raw_df, category_mapping=self.category_mapping)
        raw_df = raw_df.reset_index(drop=True)
        X_current = prep.format_ml_features(raw_df, schema=self.category_schema,
                                            feature_cols=self.feature_cols)

        # 2. Risk score + SHAP values, per scoring model (fold or final)
        group = raw_df["employee_id"].map(lambda e: self.fold_of.get(int(e), -1))
        risk = np.zeros(len(raw_df))
        shap_values = np.zeros((len(raw_df), len(self.feature_cols)))
        for k in sorted(group.unique()):
            model = self.model if k == -1 else self.fold_models[k]
            idx = np.where(group == k)[0]
            X_part = X_current.iloc[idx]
            risk[idx] = model.predict_proba(X_part)[:, 1]
            values = shap.TreeExplainer(model).shap_values(X_part)
            if isinstance(values, list):      # older shap versions: [class_0, class_1]
                values = values[1]
            shap_values[idx] = values
        raw_df["risk_score"] = risk

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
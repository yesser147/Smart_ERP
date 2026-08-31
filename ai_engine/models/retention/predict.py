import os
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
import shap

import config
from models.retention.features import fetch_raw, build_features

class RetentionModel:
    def __init__(self):
        if not os.path.exists(config.RETENTION_MODEL_PATH):
            raise FileNotFoundError(f"No trained model at {config.RETENTION_MODEL_PATH}")
        self.model = xgb.XGBClassifier()
        self.model.load_model(config.RETENTION_MODEL_PATH)

        saved = joblib.load(config.RETENTION_SCHEMA_PATH)
        self.category_schema = saved["category_schema"]
        self.feature_cols = saved["feature_cols"]
        
        # Initialize SHAP explainer for tree models
        self.explainer = shap.TreeExplainer(self.model)

    def score_all_active(self):
        raw = fetch_raw(only_active=True)
        if raw.empty:
            return raw

        raw = raw.copy()
        raw["tenure_days"] = (pd.Timestamp.now().normalize() - pd.to_datetime(raw["start_date"])).dt.days
        X = build_features(raw, schema=self.category_schema)[self.feature_cols]
        
        # Predict probability
        raw["risk_score"] = self.model.predict_proba(X)[:, 1]
        
        # Compute SHAP values for local feature attribution
        shap_values = self.explainer.shap_values(X)
        
        # Extract top 3 features driving risk UP for each employee
        top_drivers = []
        for i in range(len(raw)):
            row_shap = shap_values[i]
            # Pair feature name with SHAP value
            feature_impacts = list(zip(self.feature_cols, row_shap))
            # Sort by highest positive impact on risk
            positive_impacts = sorted([item for item in feature_impacts if item[1] > 0], key=lambda x: x[1], reverse=True)[:3]
            
            # Formatted list of top drivers (e.g., [("avg_engagement_score", "+28%"), ...])
            total_pos = sum([val for _, val in positive_impacts]) or 1.0
            drivers_formatted = [
                {"feature": feat, "impact_pct": round((val / total_pos) * 100, 1)} 
                for feat, val in positive_impacts
            ]
            top_drivers.append(drivers_formatted)
            
        raw["top_risk_drivers"] = top_drivers
        return raw

    def score_employee(self, employee_id):
        scored = self.score_all_active()
        match = scored[scored["employee_id"] == employee_id]
        return None if match.empty else match.iloc[0]
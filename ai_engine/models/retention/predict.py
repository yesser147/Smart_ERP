"""
Loads the trained model + saved feature schema, scores active employees.
No training happens here -- if artifacts/retention_model.json doesn't
exist yet, run `python -m models.retention.train` first.
"""

import os
import joblib
import pandas as pd
import xgboost as xgb

import config
from models.retention.features import fetch_raw, build_features


class RetentionModel:
    def __init__(self):
        if not os.path.exists(config.RETENTION_MODEL_PATH):
            raise FileNotFoundError(
                f"No trained model at {config.RETENTION_MODEL_PATH}. "
                f"Run `python -m models.retention.train` first."
            )
        self.model = xgb.XGBClassifier()
        self.model.load_model(config.RETENTION_MODEL_PATH)

        saved = joblib.load(config.RETENTION_SCHEMA_PATH)
        self.category_schema = saved["category_schema"]
        self.feature_cols = saved["feature_cols"]

    def score_all_active(self):
        """Returns a DataFrame: employee_id, risk_score (0-1), plus the
        raw features, for every currently-active employee."""
        raw = fetch_raw(only_active=True)
        if raw.empty:
            return raw.assign(risk_score=[])

        raw = raw.copy()
        # build_features() computes this on its own internal copy of the
        # frame -- recompute it here too so it's actually present on the
        # row diagnostic.py reads (employee_row.get("tenure_days")).
        raw["tenure_days"] = (pd.Timestamp.now().normalize() - pd.to_datetime(raw["start_date"])).dt.days

        X = build_features(raw, schema=self.category_schema)[self.feature_cols]
        raw["risk_score"] = self.model.predict_proba(X)[:, 1]
        return raw

    def score_employee(self, employee_id):
        scored = self.score_all_active()
        match = scored[scored["employee_id"] == employee_id]
        if match.empty:
            return None
        return match.iloc[0]


# module-level singleton so FastAPI doesn't reload the model file on
# every request -- loaded once, reused across calls
_instance = None


def get_model():
    global _instance
    if _instance is None:
        _instance = RetentionModel()
    return _instance
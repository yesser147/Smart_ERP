"""
Model monitoring: quality metrics, training date, and retraining on the
current data (admin page of the frontend).
"""

import json
import os
import threading
from datetime import datetime, timezone

import config

_training = threading.Lock()


class RetrainBusy(Exception):
    pass


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _trained_at(path):
    if not os.path.exists(path):
        return None
    return datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).isoformat()


def status() -> dict:
    retention = _read_json(config.RETENTION_METRICS_PATH)
    budget = _read_json(config.BUDGET_METRICS_PATH)
    return {
        "retention": {
            "name": "Attrition risk (XGBoost classifier)",
            "trained_at": _trained_at(config.RETENTION_MODEL_PATH),
            "metrics": retention,
        },
        "budget": {
            "name": "Training budget -> performance (XGBoost regressor)",
            "trained_at": _trained_at(config.BUDGET_MODEL_PATH),
            "metrics": budget,
        },
        "training": _training.locked(),
    }


def retrain() -> dict:
    """Retrains both models on the current database (about 10-30 s)."""
    if not _training.acquire(blocking=False):
        raise RetrainBusy("A training is already running.")
    try:
        from models.retention.train import train_model
        from models.budget_advisor.train import train_budget_model
        train_model()
        train_budget_model()
        return status()
    finally:
        _training.release()

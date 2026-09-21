import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    precision_score, recall_score,
)

import config
from models.retention import preprocess as prep

SEED = 42
THRESHOLD = 0.70  # threshold used by the macro strategy
SUSPICIOUS = ("status", "termination", "exit", "deleted", "churn", "reason")


def make_model():
    """Same hyperparameters as train.py."""
    return xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        enable_categorical=True,
        eval_metric="logloss",
        random_state=SEED,
    )


def oof_proba(X, y):
    """Out-of-fold probabilities: each employee is scored by a model that never saw them."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    proba = cross_val_predict(make_model(), X, y, cv=cv, method="predict_proba")[:, 1]
    fold_auc = [roc_auc_score(y[te], proba[te]) for _, te in cv.split(X, y)]
    return proba, fold_auc


def report(name, y, p):
    base = y.mean()
    auc = roc_auc_score(y, p)
    ap = average_precision_score(y, p)
    brier = brier_score_loss(y, p)
    print(f"{name:34s} AUC={auc:.3f}  PR-AUC={ap:.3f} (base {base:.3f})  "
          f"Brier={brier:.3f} (base {base * (1 - base):.3f})")
    return auc


def threshold_table(y, p):
    print("\nPrecision / recall by threshold (out-of-fold):")
    print("  thr   flagged  precision  recall")
    for t in (0.3, 0.5, THRESHOLD):
        flagged = (p >= t).astype(int)
        print(f"  {t:.2f}  {int(flagged.sum()):7d}  "
              f"{precision_score(y, flagged, zero_division=0):9.3f}  "
              f"{recall_score(y, flagged, zero_division=0):6.3f}")


def calibration_table(y, p):
    df = pd.DataFrame({"p": p, "y": y})
    df["bin"] = pd.cut(df["p"], bins=[0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0], include_lowest=True)
    t = df.groupby("bin", observed=True).agg(
        n=("y", "size"), predicted=("p", "mean"), observed=("y", "mean")
    )
    print("\nCalibration (predicted risk vs real churn rate):")
    print(t.round(3).to_string())


def main():
    print("Fetching data (active + terminated)...")
    raw = prep.fetch_raw_data(only_active=False)
    schema = prep.capture_text_categories(raw)
    X = prep.format_ml_features(raw, schema=schema).reset_index(drop=True)
    y = prep.is_churned(raw["employee_status"]).astype(int).reset_index(drop=True).values
    status = raw["employee_status"].fillna("").str.upper().reset_index(drop=True)
    is_active = status.isin(["ACTIVE", "ON LEAVE"]).values

    n, n_left = len(y), int(y.sum())
    print(f"Rows: {n} | churned: {n_left} ({y.mean():.1%}) | active: {int(is_active.sum())}")
    print(f"Features: {list(X.columns)}")

    sus = [c for c in X.columns if any(s in c.lower() for s in SUSPICIOUS)]
    if sus:
        print(f"WARNING: features that look like the label: {sus}")
    if n_left < 20 or (n - n_left) < 20:
        print("Not enough examples of one class to validate. Stopping.")
        return

    print("\n=== 1. Out-of-fold performance (5-fold, unseen employees) ===")
    p, fold_auc = oof_proba(X, y)
    auc_real = report("Real model", y, p)
    print(f"AUC per fold: {[round(a, 3) for a in fold_auc]}")

    print("\n=== 2. Noise floor: same model with shuffled labels ===")
    rng = np.random.default_rng(0)
    p_shuf, _ = oof_proba(X, rng.permutation(y))
    report("Shuffled labels (should be ~0.5)", y, p_shuf)

    if "department_turnover_rate" in X.columns:
        print("\n=== 3. Leakage check: drop department_turnover_rate ===")
        p_abl, _ = oof_proba(X.drop(columns=["department_turnover_rate"]), y)
        auc_abl = report("Without department_turnover_rate", y, p_abl)
        print(f"AUC change: {auc_abl - auc_real:+.3f}")

    threshold_table(y, p)
    calibration_table(y, p)

    top = np.argsort(-p)[: max(1, n // 10)]
    print(f"\nTop 10% riskiest: {y[top].mean():.1%} really left vs {y.mean():.1%} overall "
          f"(lift {y[top].mean() / y.mean():.1f}x)")

    print("\n=== 4. Risk scores of ACTIVE employees: in-sample vs honest ===")
    final = make_model().fit(X, y)
    p_in = final.predict_proba(X)[:, 1]
    for label, probs in (("In-sample (what the app shows)", p_in[is_active]),
                         ("Out-of-fold (honest)", p[is_active])):
        print(f"{label:32s} mean risk={probs.mean():.3f} | "
              f">= {THRESHOLD:.2f}: {(probs >= THRESHOLD).mean():.1%} of active employees")


if __name__ == "__main__":
    main()
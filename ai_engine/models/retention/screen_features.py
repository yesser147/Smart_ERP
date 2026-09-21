import numpy as np
import pandas as pd
from sqlalchemy import text
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

from database import engine
from models.retention import preprocess as prep

SEED = 42
# Columns that describe the outcome itself: using them would be leakage
LEAKY = ("status", "termination", "exit", "deleted", "reason", "churn", "end_date")

with engine.connect() as conn:
    df = pd.read_sql(text("SELECT * FROM employees WHERE is_deleted = FALSE;"), conn)

y = prep.is_churned(df["employee_status"]).astype(int).values
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
n = len(df)
print(f"Employees: {n} | churned: {y.mean():.1%}\n")


def as_numeric(s, name):
    """Numeric version of a column, or None if it is really categorical."""
    if pd.api.types.is_datetime64_any_dtype(s) or any(k in name for k in ("date", "dob", "birth")):
        d = pd.to_datetime(s, errors="coerce")
        return (d - pd.Timestamp("1970-01-01")).dt.days.astype(float)
    num = pd.to_numeric(s, errors="coerce")
    return num if num.notna().mean() > 0.9 else None


def oof_target_encoding_auc(cat, y):
    """AUC of a categorical column, each employee scored from OTHER employees only."""
    cat = cat.astype(str).values
    scores = np.zeros(len(y))
    for tr, te in cv.split(cat.reshape(-1, 1), y):
        rate = pd.Series(y[tr]).groupby(cat[tr]).mean()
        scores[te] = pd.Series(cat[te]).map(rate).fillna(y[tr].mean()).values
    return roc_auc_score(y, scores)


rows = []
for col in df.columns:
    name = col.lower()
    if any(k in name for k in LEAKY):
        continue
    s = df[col]
    nun = s.nunique(dropna=True)
    if nun <= 1 or nun > 0.5 * n:  # constant, or an id / name / email
        continue
    try:
        num = as_numeric(s, name)
        if num is not None:
            a = roc_auc_score(y, num.fillna(num.median()))
            rows.append((col, "numeric", nun, max(a, 1 - a)))
        else:
            rows.append((col, "categorical", nun, oof_target_encoding_auc(s.fillna("Unknown"), y)))
    except Exception as e:
        print(f"skipped {col}: {e}")

res = pd.DataFrame(rows, columns=["column", "type", "distinct", "auc"]).sort_values("auc", ascending=False)
print(res.round(3).to_string(index=False))
print("\nWith ~3000 rows, AUC within 0.50 +/- 0.03 is noise. Look for values clearly above 0.55.")
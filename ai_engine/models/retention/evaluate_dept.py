import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

from models.retention import preprocess as prep

SEED = 42

raw = prep.fetch_raw_data(only_active=False)
y = prep.is_churned(raw["employee_status"]).astype(int).values
dept = raw["department_id"].values

sizes = raw.groupby("department_id").size()
print(f"Departments: {len(sizes)} | median size: {sizes.median():.0f} | "
      f"size 1-2: {(sizes <= 2).sum()}")

# 1) The feature as the model sees it (contains the employee's own exit)
leaky = pd.to_numeric(raw["department_turnover_rate"], errors="coerce").fillna(0)
print(f"\nLeaky feature alone:      AUC = {roc_auc_score(y, leaky):.3f}")

# 2) Honest department base rate: computed only from OTHER employees
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
aucs = []
for tr, te in cv.split(dept.reshape(-1, 1), y):
    rate = pd.Series(y[tr]).groupby(dept[tr]).mean()
    score = pd.Series(dept[te]).map(rate).fillna(y[tr].mean()).values
    aucs.append(roc_auc_score(y[te], score))
print(f"Honest department rate:   AUC = {sum(aucs) / len(aucs):.3f} "
      f"(folds: {[round(a, 3) for a in aucs]})")
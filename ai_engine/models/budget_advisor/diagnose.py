import pandas as pd
import xgboost as xgb
from sklearn.model_selection import KFold, cross_val_score
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from database import engine

FEATURES = ['training_budget', 'headcount', 'avg_engagement', 'department_turnover_rate']
TARGET = 'avg_performance'

df = pd.read_sql("SELECT * FROM v_ai_training_budget_features;", engine).dropna(subset=[TARGET])
df[FEATURES] = df[FEATURES].fillna(0)
X, y = df[FEATURES], df[TARGET]

print("Target spread:")
print(y.describe().round(3))
print("\nCorrelation with target:")
print(df[FEATURES + [TARGET]].corr()[TARGET].round(3))

cv = KFold(n_splits=5, shuffle=True, random_state=42)
models = {
    "Mean baseline": DummyRegressor(strategy="mean"),
    "Ridge (linear)": make_pipeline(StandardScaler(), Ridge(alpha=10)),
    "RandomForest": RandomForestRegressor(n_estimators=200, min_samples_leaf=20, random_state=42),
    "XGB shallow": xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=2,
                                    min_child_weight=20, random_state=42),
}

print("\nCross-validated R2:")
for name, m in models.items():
    r2 = cross_val_score(m, X, y, cv=cv, scoring="r2")
    print(f"{name:16s} {r2.mean():.3f} (+/- {r2.std():.3f})")
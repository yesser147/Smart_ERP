"""
Retention curves (survival analysis): the share of people still employed
N years after joining, per department, with the Kaplan-Meier estimator.

Unlike the attrition classifier, it handles employees who are still here
correctly: their tenure is "at least N years" (censored), not a final value.
"""

import numpy as np
import pandas as pd
from sqlalchemy import text

from database import engine
from models.retention.preprocess import is_churned

MAX_YEARS = 10


def kaplan_meier(durations: np.ndarray, events: np.ndarray, horizon: int = MAX_YEARS) -> list[float]:
    """S(t) at t = 0..horizon years. durations in years; events 1 = left, 0 = still employed."""
    order = np.argsort(durations)
    durations, events = durations[order], events[order]
    survival, curve = 1.0, []
    grid = np.arange(0, horizon + 1)
    at_risk = len(durations)
    i = 0
    for t in grid:
        while i < len(durations) and durations[i] <= t:
            # all people with the same duration leave the risk set together
            same = durations == durations[i]
            d = int(events[same].sum())
            n = int(same.sum())
            if at_risk > 0 and d > 0:
                survival *= 1 - d / at_risk
            at_risk -= n
            i += n
        curve.append(round(float(survival) * 100, 1))
    return curve


def retention_curves() -> dict:
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT d.department_type, e.start_date, e.exit_date, e.employee_status
            FROM employees e JOIN departments d ON d.department_id = e.department_id
            WHERE e.is_deleted = FALSE AND e.start_date IS NOT NULL
              AND UPPER(COALESCE(e.employee_status, '')) <> 'FUTURE START'
        """), conn)
    if df.empty:
        return {"years": list(range(MAX_YEARS + 1)), "series": []}

    today = pd.Timestamp.now().normalize()
    left = is_churned(df["employee_status"]).to_numpy().astype(int)
    end = pd.to_datetime(df["exit_date"]).fillna(today).clip(upper=today)
    years = ((end - pd.to_datetime(df["start_date"])).dt.days / 365.25).clip(lower=0).to_numpy()

    series = [{"name": "Company", "values": kaplan_meier(years, left), "employees": int(len(df))}]
    for dept, idx in df.groupby("department_type").groups.items():
        rows = np.array(list(idx))
        pos = df.index.get_indexer(rows)
        series.append({"name": dept, "values": kaplan_meier(years[pos], left[pos]), "employees": int(len(pos))})

    # median tenure: first year where fewer than half are still here
    for s in series:
        below = [y for y, v in enumerate(s["values"]) if v < 50]
        s["median_years"] = below[0] if below else None
    return {"years": list(range(MAX_YEARS + 1)), "series": series}

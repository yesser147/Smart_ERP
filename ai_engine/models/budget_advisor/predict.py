import json
import joblib
import pandas as pd
import config
from database import engine

FEATURES = ['training_budget', 'headcount', 'avg_engagement', 'department_turnover_rate']
METRICS_PATH = config.BUDGET_METRICS_PATH


def _dept_label(row):
    """'Sales - Sales Executives - Team 3 (12)': department + team name,
    suffixed with department_id as the uniqueness guarantee."""
    dept_type = row.get('department_type')
    team = row.get('division_description') or row.get('business_unit')

    if dept_type and team:
        base = f"{dept_type} - {team}"
    else:
        base = dept_type or team or 'Dept'

    return f"{base} ({int(row['department_id'])})"


class BudgetPrescriptor:
    def __init__(self):
        try:
            self.model = joblib.load(config.BUDGET_MODEL_PATH)
        except FileNotFoundError:
            raise Exception("Model artifact missing. Run `python -m models.budget_advisor.train` first.")

        try:
            with open(METRICS_PATH, encoding='utf-8') as f:
                self._metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._metrics = {}

        self._df_cache = None

    def _load_features(self):
        if self._df_cache is None:
            df = pd.read_sql("SELECT * FROM v_ai_training_budget_features;", engine)
            # Same preparation as train.py: real averages only
            df = df.dropna(subset=['avg_performance'])
            df = df[df['headcount'] >= self._metrics.get('min_headcount', 1)].copy()
            df[FEATURES] = df[FEATURES].fillna(df[FEATURES].median())
            self._df_cache = df.reset_index(drop=True)
        return self._df_cache

    def _budget_curve(self, row, curve_points: int = 25):
        """Single source of truth for the performance/budget curve and its
        peak. Used by the charts AND the recommendations table."""
        current_budget = float(row['training_budget'])
        base_perf = float(row['predicted_current_perf'])

        # Stay inside the budget range the model has seen in training
        observed_max = float(self._metrics.get('budget_max', current_budget + 30000.0))
        slider_max = round(max(observed_max, current_budget), 2)
        if slider_max <= 0:
            slider_max = 1000.0

        budgets = [round(slider_max * i / (curve_points - 1), 2) for i in range(curve_points)]
        X_curve = pd.DataFrame([row[FEATURES].copy()] * curve_points).reset_index(drop=True)
        X_curve['training_budget'] = budgets
        curve_preds = self.model.predict(X_curve)

        curve = [
            {"budget": b, "performance": round(float(p), 4)}
            for b, p in zip(budgets, curve_preds)
        ]
        peak = max(curve, key=lambda p: p["performance"])

        # If the current budget beats every grid point, keep it
        if base_perf > peak["performance"]:
            peak = {"budget": round(current_budget, 2), "performance": round(base_perf, 4)}

        return slider_max, curve, peak

    def _optimal_summary(self, dept_row, group):
        current_budget = float(dept_row['training_budget'])
        current_perf = round(float(dept_row['predicted_current_perf']), 3)
        _, _, peak = self._budget_curve(dept_row)

        return {
            "department_id": int(dept_row['department_id']),
            "department_name": _dept_label(dept_row),
            "group": group,  # 'top' or 'bottom'
            "current_budget": current_budget,
            "current_performance": current_perf,
            "optimal_budget": peak["budget"],
            "optimal_performance": peak["performance"],
            "budget_change": round(peak["budget"] - current_budget, 2),  # can be negative
            "performance_gain": round(peak["performance"] - current_perf, 3),
        }

    def calculate_elasticity_and_charts(self):
        df = self._load_features()

        if df.empty:
            return df, [], [], []

        X_current = df[FEATURES]
        df['predicted_current_perf'] = self.model.predict(X_current)

        # Bottom 3 and top 3 by current predicted performance (no overlap)
        worst_depts = df.nsmallest(3, 'predicted_current_perf')
        best_depts = df.drop(worst_depts.index).nlargest(3, 'predicted_current_perf')

        worst_depts_analysis = (
            [self._optimal_summary(r, 'top') for _, r in best_depts.iterrows()]
            + [self._optimal_summary(r, 'bottom') for _, r in worst_depts.iterrows()]
        )

        X_simulated = X_current.copy()
        X_simulated['training_budget'] += 5000.00
        df['predicted_simulated_perf'] = self.model.predict(X_simulated)
        df['performance_gain'] = df['predicted_simulated_perf'] - df['predicted_current_perf']
        df = df.sort_values(by='performance_gain', ascending=False)

        comparison_chart = []
        for _, row in df.iterrows():
            comparison_chart.append({
                "department_id": int(row['department_id']),
                "department_name": _dept_label(row),
                "current_budget": float(row['training_budget']),
                "current_performance": round(float(row['predicted_current_perf']), 2),
                "simulated_performance": round(float(row['predicted_simulated_perf']), 2),
                "performance_gain": round(float(row['performance_gain']), 3)
            })

        budget_steps = [0, 2500, 5000, 7500, 10000, 15000, 20000]
        sensitivity_curve = []

        for step in budget_steps:
            point_data = {"added_budget": f"+${step:,}"}
            X_step = X_current.copy()
            X_step['training_budget'] += step
            preds = pd.Series(self.model.predict(X_step), index=X_step.index)

            for idx, row in df.iterrows():
                point_data[_dept_label(row)] = round(float(preds.loc[idx]), 3)

            sensitivity_curve.append(point_data)

        return df, comparison_chart, sensitivity_curve, worst_depts_analysis

    def get_department_baselines(self, curve_points: int = 25):
        df = self._load_features()
        if df.empty:
            return []

        X_current = df[FEATURES]
        df = df.copy()
        df['predicted_current_perf'] = self.model.predict(X_current)

        baselines = []
        for _, row in df.iterrows():
            current_budget = float(row['training_budget'])
            slider_max, curve, peak = self._budget_curve(row, curve_points)

            baselines.append({
                "department_id": int(row['department_id']),
                "department_name": _dept_label(row),
                "department_type": row.get('department_type'),
                "business_unit": row.get('business_unit'),
                "division_description": row.get('division_description'),
                "current_budget": current_budget,
                "current_performance": round(float(row['predicted_current_perf']), 3),
                "slider_min": 0.0,
                "slider_max": slider_max,
                "curve": curve,
                "peak_budget": peak["budget"],
                "peak_performance": peak["performance"],
            })
        return baselines

    def simulate_single_department(self, department_id: int, new_total_budget: float):
        """Live what-if: exact prediction for one specific budget value,
        called on every debounced slider drag. The curve above is for
        visualization; this is the precise number shown to the user."""
        df = self._load_features()
        match = df[df['department_id'] == department_id]
        if match.empty:
            return None

        dept_row = match.iloc[0]
        base_perf = float(self.model.predict(pd.DataFrame([dept_row[FEATURES]]))[0])

        X_sim = pd.DataFrame([dept_row[FEATURES].copy()])
        X_sim['training_budget'] = new_total_budget
        simulated_perf = float(self.model.predict(X_sim)[0])

        return {
            "department_id": int(dept_row['department_id']),
            "department_name": _dept_label(dept_row),
            "current_budget": float(dept_row['training_budget']),
            "current_performance": round(base_perf, 3),
            "simulated_budget": float(new_total_budget),
            "simulated_performance": round(simulated_perf, 3),
            "performance_gain": round(simulated_perf - base_perf, 3),
        }
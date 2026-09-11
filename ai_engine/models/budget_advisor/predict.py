import joblib
import pandas as pd
from database import engine

FEATURES = ['training_budget', 'headcount', 'avg_engagement', 'department_turnover_rate']


def _dept_label(row):
    """department_type is a broad category (e.g. 'Sales') that many
    departments share; business_unit (e.g. 'PL', 'EW', 'TNS') is what
    actually distinguishes them. Combine both when available so labels
    read as 'Sales - TNS (#19)' instead of two identical-looking
    'Sales (#19)' / 'Sales (#20)' entries that only differ by id.
    Still always suffixed with department_id as the uniqueness
    guarantee regardless of how the type/unit combination reads."""
    dept_type = row.get('department_type')
    unit = row.get('business_unit')

    if dept_type and unit:
        base = f"{dept_type} - {unit}"
    else:
        base = dept_type or unit or 'Dept'

    return f"{base} (#{int(row['department_id'])})"


class BudgetPrescriptor:
    def __init__(self):
        try:
            self.model = joblib.load('models/budget/saved_models/budget_xgboost.pkl')
        except FileNotFoundError:
            raise Exception("Model artifact missing. Run models/budget/train.py first.")
        self._df_cache = None

    def _load_features(self):
        if self._df_cache is None:
            query = "SELECT * FROM v_ai_training_budget_features;"
            self._df_cache = pd.read_sql(query, engine).fillna(0)
        return self._df_cache

    def calculate_elasticity_and_charts(self):
        df = self._load_features()

        if df.empty:
            return df, [], [], []

        X_current = df[FEATURES]
        df['predicted_current_perf'] = self.model.predict(X_current)

        worst_depts = df.nsmallest(3, 'predicted_current_perf')
        worst_depts_analysis = []
        budget_variations = [1000, 2500, 5000, 7500, 10000, 15000, 20000]

        for _, dept_row in worst_depts.iterrows():
            dept_name = _dept_label(dept_row)
            base_perf = float(dept_row['predicted_current_perf'])
            base_budget = float(dept_row['training_budget'])

            dept_tests = []
            for step in budget_variations:
                X_sim = pd.DataFrame([dept_row[FEATURES].copy()])
                X_sim['training_budget'] += step

                simulated_perf = float(self.model.predict(X_sim)[0])
                gain = round(simulated_perf - base_perf, 4)

                dept_tests.append({
                    "added_budget": step,
                    "total_budget": base_budget + step,
                    "performance_gain": gain
                })

            worst_depts_analysis.append({
                "department_id": int(dept_row['department_id']),
                "department_name": dept_name,
                "current_budget": base_budget,
                "current_performance": round(base_perf, 3),
                "price_variations_tested": dept_tests
            })

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
        """Feeds the what-if slider UI: current budget/performance, slider
        range, AND a full performance-vs-budget curve per department so
        the frontend can paint the 'altitude' gradient along the track
        and mark the exact peak (highest predicted performance point).

        Each department still costs exactly one model.predict() call --
        it's vectorized across curve_points budget levels, not one call
        per point."""
        df = self._load_features()
        if df.empty:
            return []

        X_current = df[FEATURES]
        df = df.copy()
        df['predicted_current_perf'] = self.model.predict(X_current)

        baselines = []
        for _, row in df.iterrows():
            current_budget = float(row['training_budget'])
            slider_max = round(current_budget + 30000.0, 2)

            budgets = [round(slider_max * i / (curve_points - 1), 2) for i in range(curve_points)]
            X_curve = pd.DataFrame([row[FEATURES].copy()] * curve_points).reset_index(drop=True)
            X_curve['training_budget'] = budgets
            curve_preds = self.model.predict(X_curve)

            curve = [
                {"budget": b, "performance": round(float(p), 4)}
                for b, p in zip(budgets, curve_preds)
            ]
            peak = max(curve, key=lambda p: p["performance"])

            baselines.append({
                "department_id": int(row['department_id']),
                "department_name": _dept_label(row),
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
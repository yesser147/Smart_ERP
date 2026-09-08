import joblib
import pandas as pd
from database import engine

FEATURES = ['training_budget', 'headcount', 'avg_engagement', 'department_turnover_rate']


def _dept_label(row):
    """Always suffixed with the unique department_id. department_type
    (and even business_unit) can repeat across different departments --
    using it alone as a chart series name/dict key silently collides and
    drops data whenever two departments share a type. See the added_budget
    sensitivity loop below for where that actually bites."""
    base = row.get('department_type') or row.get('business_unit') or 'Dept'
    return f"{base} (#{int(row['department_id'])})"


class BudgetPrescriptor:
    def __init__(self):
        try:
            self.model = joblib.load('models/budget/saved_models/budget_xgboost.pkl')
        except FileNotFoundError:
            raise Exception("Model artifact missing. Run models/budget/train.py first.")

    def calculate_elasticity_and_charts(self):
        query = "SELECT * FROM v_ai_training_budget_features;"
        df = pd.read_sql(query, engine).fillna(0)

        if df.empty:
            return df, [], [], []

        # 1. Baseline Performance Prediction
        X_current = df[FEATURES]
        df['predicted_current_perf'] = self.model.predict(X_current)

        # 2. Identify the BOTTOM 3 Worst-Performing Departments
        worst_depts = df.nsmallest(3, 'predicted_current_perf')
        worst_depts_analysis = []
        budget_variations = [1000, 2500, 5000, 7500, 10000, 15000, 20000]

        # 3. Test Multiple Price Variations on these 3 Departments
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

        # 4. Standard Department Comparison Bar Chart ($5k default)
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
            # .loc keyed by X_step's own index, not raw positional --
            # preds[idx] worked before only because nothing filtered df
            # upstream, so index labels happened to equal positions. Any
            # future .dropna()/filter added before this point would have
            # silently broken that assumption.
            preds = pd.Series(self.model.predict(X_step), index=X_step.index)

            for idx, row in df.iterrows():
                point_data[_dept_label(row)] = round(float(preds.loc[idx]), 3)

            sensitivity_curve.append(point_data)

        return df, comparison_chart, sensitivity_curve, worst_depts_analysis
import joblib
import pandas as pd
from database import engine

FEATURES = ['training_budget', 'headcount', 'avg_engagement', 'department_turnover_rate']

class BudgetPrescriptor:
    def __init__(self):
        try:
            self.model = joblib.load('models/budget/saved_models/budget_xgboost.pkl')
        except FileNotFoundError:
            raise Exception("Model artifact missing. Run models/budget/train.py first.")

    def calculate_elasticity_and_charts(self):
        """Generates headline metrics plus multi-point simulation data for frontend charts."""
        query = "SELECT * FROM v_ai_training_budget_features;"
        df = pd.read_sql(query, engine).fillna(0)

        if df.empty:
            return df, [], []

        # 1. Headline Elasticity ($5,000 simulation)
        X_current = df[FEATURES]
        df['predicted_current_perf'] = self.model.predict(X_current)

        X_simulated = X_current.copy()
        X_simulated['training_budget'] += 5000.00
        df['predicted_simulated_perf'] = self.model.predict(X_simulated)
        df['performance_gain'] = df['predicted_simulated_perf'] - df['predicted_current_perf']
        
        df = df.sort_values(by='performance_gain', ascending=False)

        # 2. Graph Data 1: Department Comparison Bar Chart
        comparison_chart = []
        for _, row in df.iterrows():
            dept_name = row.get('department_type') or f"Dept #{int(row['department_id'])}"
            comparison_chart.append({
                "department_id": int(row['department_id']),
                "department_name": dept_name,
                "current_budget": float(row['training_budget']),
                "current_performance": round(float(row['predicted_current_perf']), 2),
                "simulated_performance": round(float(row['predicted_simulated_perf']), 2),
                "performance_gain": round(float(row['performance_gain']), 3)
            })

        # 3. Graph Data 2: Budget Sensitivity Curve (Multi-point prediction)
        budget_steps = [0, 2500, 5000, 7500, 10000, 15000, 20000]
        sensitivity_curve = []

        for step in budget_steps:
            point_data = {"added_budget": f"+${step:,}"}
            X_step = X_current.copy()
            X_step['training_budget'] += step
            preds = self.model.predict(X_step)

            for idx, row in df.iterrows():
                dept_name = row.get('department_type') or f"Dept #{int(row['department_id'])}"
                point_data[dept_name] = round(float(preds[idx]), 3)

            sensitivity_curve.append(point_data)

        return df, comparison_chart, sensitivity_curve
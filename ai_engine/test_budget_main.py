import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from models.budget_advisor.train import train_budget_model
from models.budget_advisor.predict import BudgetPrescriptor
from models.budget_advisor.advise import generate_budget_proposal

def main():
    print("=== AI SERVICE 2: TRAINING BUDGET PRESCRIPTIVE ADVISOR ===\n")
    
    print("[Step 1/3] Training XGBoost Regressor...")
    train_budget_model()

    print("\n[Step 2/3] Simulating Budget Elasticity & Multi-Point Curves...")
    prescriptor = BudgetPrescriptor()
    elasticity_df, comparison_chart, sensitivity_curve = prescriptor.calculate_elasticity_and_charts()

    if elasticity_df.empty:
        print("Error: No data available for elasticity analysis.")
        return

    print("\n[Step 3/3] Generating Executive Allocation Proposal & Chart AI Deductions...\n")
    payload = generate_budget_proposal(elasticity_df, comparison_chart, sensitivity_curve)

    # ---------------------------------------------------------
    # PRINTING THE INTERPRETED RESULTS FOR HUMAN READABILITY
    # ---------------------------------------------------------
    print("================ AI INTERPRETED RESULTS ================")
    
    print("\n📝 EXECUTIVE MEMO:")
    print(f"   {payload.get('executive_proposal_memo', 'No memo generated.')}")
    
    print("\n📊 AI CHART DEDUCTIONS (Data Interpretation):")
    for idx, insight in enumerate(payload.get('chart_insights', []), 1):
        print(f"   {idx}. {insight}")

    print("\n💰 RECOMMENDED ALLOCATIONS:")
    for alloc in payload.get('recommended_allocations', []):
        dept = alloc.get('department_name', 'Unknown')
        increase = alloc.get('recommended_budget_increase', 0)
        gain = alloc.get('expected_performance_gain', 0)
        print(f"   - {dept}: +${increase:,} (Expected Gain: +{gain})")

    print("\n========================================================")
    
    # Optional: Still show the raw frontend payload structure (truncated to save space)
    print("\n[Debug] Raw JSON Payload sample being sent to frontend:")
    debug_payload = {
        "recommended_allocations": payload.get("recommended_allocations"),
        "chart_insights": payload.get("chart_insights"),
        "chart_data_keys": list(payload.get("chart_data", {}).keys()) # Just showing the keys so it doesn't flood the terminal
    }
    print(json.dumps(debug_payload, indent=4))

if __name__ == "__main__":
    main()
import pandas as pd
from models.retention.predict import RetentionModel
from models.retention.diagnostic import generate_diagnostic, fetch_recent_exit_reasons

def test_upgraded_retention_service():
    print("1. Loading XGBoost model & running SHAP feature attribution...")
    model = RetentionModel()
    df = model.score_all_active()

    if df.empty:
        print("Error: No active employees fetched from PostgreSQL.")
        return

    print(f"Successfully scored {len(df)} active employees.")

    # Select the highest-risk employee for verification
    target_emp = df.sort_values(by="risk_score", ascending=False).iloc[0]
    
    print("\n================ TARGET EMPLOYEE ================")
    print(f"Employee ID:   {target_emp['employee_id']}")
    print(f"Business Unit: {target_emp['business_unit']}")
    print(f"Risk Score:    {target_emp['risk_score'] * 100:.2f}%")

    print("\n================ SHAP RISK DRIVERS ================")
    drivers = target_emp.get("top_risk_drivers", [])
    if drivers:
        for d in drivers:
            print(f" -> {d['feature']}: {d['impact_pct']}% impact")
    else:
        print("No positive SHAP drivers identified.")

    print("\n================ HISTORICAL EXIT NOTES ================")
    exit_notes = fetch_recent_exit_reasons(target_emp['business_unit'])
    if exit_notes:
        for i, note in enumerate(exit_notes, 1):
            print(f" [{i}] {note}")
    else:
        print("No historical exit notes found for this business unit.")

    print("\n================ GENERATING AI DIAGNOSTIC ================")
    diagnostic = generate_diagnostic(target_emp)
    print("\n" + diagnostic)

if __name__ == "__main__":
    test_upgraded_retention_service()
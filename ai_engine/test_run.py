from models.retention.predict import get_model
from models.retention.diagnostic import generate_diagnostic

# 1. Load model and score active workforce
model = get_model()
scored_df = model.score_all_active()

print(f"Scored {len(scored_df)} active employees.")
print(scored_df[["employee_id", "business_unit", "risk_score"]].head())

# 2. Select the highest-risk employee and generate an LLM diagnostic memo
if not scored_df.empty:
    top_risk_employee = scored_df.sort_values(by="risk_score", ascending=False).iloc[0]
    
    print(f"\n--- AI Diagnostic for Employee: {top_risk_employee['employee_id']} ---")
    print(f"Risk Score: {round(top_risk_employee['risk_score'] * 100, 1)}%\n")
    
    diagnostic_text = generate_diagnostic(top_risk_employee)
    print(diagnostic_text)
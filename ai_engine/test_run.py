import pandas as pd

# Import the refactored modular pipeline
from models.retention.train import train_model
from models.retention.predict import RetentionPredictor
from models.retention.diagnostic import generate_manager_report

def run_pipeline():
    print("=== RUNNING END-TO-END RETENTION AI PIPELINE ===")
    
    # ---------------------------------------------------------
    # PHASE 1: Train the model on historical data
    # ---------------------------------------------------------
    print("\n--- PHASE 1: TRAINING THE XGBOOST MODEL ---")
    train_model()
    
    # ---------------------------------------------------------
    # PHASE 2: Score current active employees using math (SHAP)
    # ---------------------------------------------------------
    print("\n--- PHASE 2: SCORING CURRENT EMPLOYEES ---")
    predictor = RetentionPredictor()
    scored_employees = predictor.analyze_active_employees()
    
    if scored_employees.empty:
        print("Error: No active employees found in the database.")
        return
        
    print(f"Successfully calculated risk scores for {len(scored_employees)} employees.")
    
    # ---------------------------------------------------------
    # PHASE 3: Isolate the highest risk employee
    # ---------------------------------------------------------
    # Sort the dataframe so the highest risk_score is at the top (index 0)
    high_risk_df = scored_employees.sort_values(by="risk_score", ascending=False)
    target_employee = high_risk_df.iloc[0]
    
    print("\n--- PHASE 3: HIGHEST RISK EMPLOYEE IDENTIFIED ---")
    print(f"Employee ID:   {target_employee.get('employee_id', 'Unknown')}")
    print(f"Department:    {target_employee.get('business_unit', 'Unknown')}")
    print(f"Risk Score:    {target_employee['risk_score'] * 100:.1f}%\n")
    
    print("Top Mathematical Drivers (SHAP):")
    for driver in target_employee['top_risk_drivers']:
        print(f" -> {driver['feature']}: {driver['impact_pct']}% impact")

    # ---------------------------------------------------------
    # PHASE 4: Feed data to LLaMA for Generative Synthesis
    # ---------------------------------------------------------
    print("\n--- PHASE 4: GENERATING LLaMA HR DIAGNOSTIC ---")
    print("Sending context to NVIDIA NIM (LLaMA 3.1)...")
    
    final_report = generate_manager_report(target_employee)
    
    print("\n================ FINAL AI REPORT ================\n")
    print(final_report)
    print("\n=================================================")

if __name__ == "__main__":
    run_pipeline()
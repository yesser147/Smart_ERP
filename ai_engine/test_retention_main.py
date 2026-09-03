import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.retention.train import train_model
from models.retention.predict import RetentionPredictor
from models.retention.diagnostic import generate_macro_retention_strategy

# Define the flight risk threshold (70% score)
RISK_THRESHOLD = 0.70 

def run_pipeline():
    print("=== RUNNING MACRO RETENTION AI PIPELINE ===")
    
    print("\n[Step 1/3] TRAINING THE XGBOOST MODEL...")
    train_model()
    
    print("\n[Step 2/3] SCORING ALL ACTIVE EMPLOYEES...")
    predictor = RetentionPredictor()
    scored_employees = predictor.analyze_active_employees()
    
    if scored_employees.empty:
        print("Error: No active employees found in the database.")
        return
        
    total_active = len(scored_employees)
    print(f"Successfully evaluated {total_active} active employees.")
    
    # Filter by risk threshold (e.g. risk_score >= 0.70)
    high_risk_df = scored_employees[scored_employees["risk_score"] >= RISK_THRESHOLD]
    
    # Graceful Fallback: If no employee is >70%, take the top 10% highest-risk employees
    if high_risk_df.empty:
        print(f"Notice: No employees exceeded {int(RISK_THRESHOLD*100)}% risk. Analyzing top 10% highest risk instead.")
        top_10_percent_count = max(1, int(total_active * 0.10))
        high_risk_df = scored_employees.sort_values(by="risk_score", ascending=False).head(top_10_percent_count)

    high_risk_pct = round((len(high_risk_df) / total_active) * 100, 1)
    
    print("\n[Step 3/3] ANALYZING MACRO AT-RISK COHORT...")
    
    high_risk_count = len(high_risk_df)
    print(f" -> High-Risk Count: {high_risk_count} / {total_active} ({high_risk_pct}% of total workforce)")

    # --- NEW: PRINT THE RAW SHAP AGGREGATIONS FOR THE USER TO SEE ---
    if high_risk_count > 0:
        print("\n⚙️ RAW ML SHAP DRIVERS (What the AI is analyzing):")
        driver_counts = {}
        for drivers in high_risk_df["top_risk_drivers"]:
            for d in drivers:
                feat = d['feature']
                driver_counts[feat] = driver_counts.get(feat, 0) + 1
                
        for feat, count in sorted(driver_counts.items(), key=lambda x: x[1], reverse=True):
            pct_of_high_risk = round((count / high_risk_count) * 100, 1)
            print(f"  - {feat}: Triggered in {pct_of_high_risk}% of high-risk employees ({count}/{high_risk_count})")
    # -----------------------------------------------------------------

    print("\nSending aggregated ML drivers & percentage trends to Groq...")
    macro_strategy = generate_macro_retention_strategy(high_risk_df, total_active, threshold=RISK_THRESHOLD)

    # ---------------------------------------------------------
    # PRINTING THE INTERPRETED RESULTS
    # ---------------------------------------------------------
    print("\n================ MACRO RETENTION STRATEGY REPORT ================\n")
    
    metrics = macro_strategy.get("macro_metrics", {})
    print("📊 WORKFORCE RISK EXPOSURE:")
    print(f"   - Total Active Workforce : {metrics.get('total_active_employees')}")
    print(f"   - High Risk Population   : {metrics.get('high_risk_count')} employees (>= {int(RISK_THRESHOLD*100)}% risk)")
    print(f"   - Workforce Exposure Rate: {metrics.get('high_risk_percentage')}%\n")
    
    print("📝 EXECUTIVE SUMMARY:")
    print(f"   {macro_strategy.get('executive_summary', '')}\n")
    
    print("🔍 GENERALIZED ROOT CAUSES (Company-Wide Drivers):")
    for idx, cause in enumerate(macro_strategy.get('generalized_root_causes', []), 1):
        print(f"   {idx}. {cause}")
        
    print("\n🛡️ STRATEGIC SYSTEMIC INTERVENTIONS:")
    for init in macro_strategy.get('systemic_interventions', []):
        print(f"   - Initiative: {init.get('initiative_name')}")
        print(f"     Action: {init.get('description')}")
        print(f"     Target Metric: {init.get('target_metric_to_improve')}\n")

    print("=================================================================")

if __name__ == "__main__":
    run_pipeline()
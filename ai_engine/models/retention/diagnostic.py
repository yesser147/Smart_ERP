import json
import pandas as pd
from sqlalchemy import text
from database import engine
from groq import Groq  # Updated import
import config

def get_cohort_exit_reasons(department_ids):
    """Pulls aggregated historical exit reasons for departments in the high-risk pool."""
    if not department_ids:
        return []
    
    valid_ids = [str(int(d)) for d in department_ids if pd.notna(d)]
    if not valid_ids:
        return []

    dept_list = ", ".join(valid_ids)
    query = text(f"""
        SELECT d.department_type, v.termination_description, SUM(v.exit_count) as total_exits
        FROM v_ai_exit_reason_frequencies v
        JOIN departments d ON d.department_id = v.department_id
        WHERE v.department_id IN ({dept_list})
        GROUP BY d.department_type, v.termination_description
        ORDER BY total_exits DESC
        LIMIT 5;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
        return [f"{row[0]} Depts - '{row[1]}' ({row[2]} past terminations)" for row in result if row[1]]

def generate_macro_retention_strategy(high_risk_df, total_active_count, threshold=0.70):
    """
    Analyzes all employees above the risk threshold, aggregates SHAP drivers into percentages,
    and prompts Groq LLM to generate a generalized company-wide strategy.
    """
    # Initialize native Groq client
    client = Groq(api_key=config.GROQ_API_KEY)
    
    high_risk_count = len(high_risk_df)
    high_risk_pct = round((high_risk_count / total_active_count) * 100, 1) if total_active_count > 0 else 0

    # 1. Aggregate SHAP Drivers across ALL high-risk employees
    driver_counts = {}
    for drivers in high_risk_df["top_risk_drivers"]:
        for d in drivers:
            feat = d['feature']
            driver_counts[feat] = driver_counts.get(feat, 0) + 1
            
    # Convert counts to percentages of the high-risk population
    driver_summary = []
    for feat, count in sorted(driver_counts.items(), key=lambda x: x[1], reverse=True):
        pct_of_high_risk = round((count / high_risk_count) * 100, 1)
        driver_summary.append(f"- {feat}: Primary risk trigger for {pct_of_high_risk}% of high-risk employees ({count}/{high_risk_count}).")

    driver_summary_str = "\n".join(driver_summary)

    # 2. Gather Historical Context for affected departments
    unique_depts = high_risk_df["department_id"].dropna().unique().tolist()
    exit_notes = get_cohort_exit_reasons(unique_depts)
    
    historical_context = ""
    if exit_notes:
        exits_text = "\n".join([f"- {note}" for note in exit_notes])
        historical_context = f"\nHistorical Exit Patterns in Affected Departments:\n{exits_text}\n"

    # 3. Prompt Groq for a Macro Strategy
    prompt = f"""You are an AI Chief HR Officer.
An XGBoost ML model analyzed the entire workforce ({total_active_count} active employees).

WORKFORCE EXPOSURE METRICS:
- Risk Threshold: Risk Score >= {int(threshold * 100)}%
- At-Risk Employee Count: {high_risk_count} out of {total_active_count} employees
- Workforce Exposure Rate: {high_risk_pct}% of total workforce is at HIGH flight risk

AGGREGATED ML RISK DRIVERS (XGBoost SHAP across high-risk population):
{driver_summary_str}
{historical_context}

Task:
Analyze these macro trends to deduce the systemic, root-cause organizational problems driving turnover. Propose strategic, high-impact interventions.

Constraints:
1. Return ONLY a valid JSON object.
2. Must match this exact structure:
{{
    "macro_metrics": {{
        "total_active_employees": {total_active_count},
        "high_risk_count": {high_risk_count},
        "high_risk_percentage": {high_risk_pct},
        "risk_threshold": {threshold}
    }},
    "executive_summary": "Summarize the workforce risk exposure and generalized core issues in 2-3 sentences.",
    "generalized_root_causes": [
        "Root cause 1 derived from dominant ML drivers and exit history",
        "Root cause 2..."
    ],
    "systemic_interventions": [
        {{
            "initiative_name": "Name of Strategic Action",
            "description": "How this initiative solves the generalized root cause",
            "target_metric_to_improve": "Metric name"
        }}
    ]
}}"""

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
            timeout=30.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"\n[API Warning] LLM Generation Failed: {str(e)}")
        return {
            "macro_metrics": {
                "total_active_employees": total_active_count,
                "high_risk_count": high_risk_count,
                "high_risk_percentage": high_risk_pct,
                "risk_threshold": threshold
            },
            "executive_summary": "Warning: AI Strategy generation failed. Review macro metrics and ML drivers manually.",
            "generalized_root_causes": [f"AI analysis temporarily unavailable: {str(e)}"],
            "systemic_interventions": []
        }
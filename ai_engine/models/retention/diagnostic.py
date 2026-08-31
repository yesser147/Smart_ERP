from sqlalchemy import text
from database import engine
from openai import OpenAI
import config

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(base_url=config.NIM_BASE_URL, api_key=config.NIM_API_KEY)
    return _client

def fetch_recent_exit_reasons(business_unit):
    """Pulls historical exit descriptions from the same business unit."""
    query = text("""
        SELECT termination_description 
        FROM v_ai_exit_reason_frequencies
        WHERE business_unit = :bu
        ORDER BY exit_count DESC
        LIMIT 3;
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"bu": business_unit}).fetchall()
        return [row[0] for row in result if row[0]]

PROMPT_TEMPLATE = """You are an HR Predictive Analytics Assistant. An XGBoost ML model calculated a {risk_pct}% flight risk for this employee.

Calculated Risk Drivers (XGBoost SHAP Feature Attribution):
{shap_drivers_text}

Employee Metrics:
- Department: {business_unit} | Job: {job_function}
- Performance Score: {performance_score} | Tenure: {tenure_days} days
- Engagement Score: {avg_engagement_score}/5 | Satisfaction: {avg_satisfaction_score}/5 | Work-Life Balance: {avg_work_life_balance}/5

Historical Exit Patterns in {business_unit} Department:
{historical_exits}

Task:
Write an executive diagnostic for the manager in 2 parts:
1. MATHEMATICAL RISK DRIVERS & HISTORICAL PATTERNS: Explain how the top calculated drivers (with percentages) correlate with historical exit trends in this department.
2. RECOMMENDED ACTION PLAN: Provide 2 specific, actionable manager interventions addressing these calculated risk drivers. Keep under 170 words total."""

def generate_diagnostic(employee_row):
    client = _get_client()
    
    # Format SHAP Drivers
    drivers = employee_row.get("top_risk_drivers", [])
    shap_text = "\n".join([f"- {d['feature']}: accounts for {d['impact_pct']}% of elevated risk" for d in drivers])
    
    # Fetch department historical exit descriptions
    bu = employee_row.get("business_unit", "")
    exit_notes = fetch_recent_exit_reasons(bu)
    exits_text = "\n".join([f"- Exit Note: '{note}'" for note in exit_notes]) if exit_notes else "- No historical notes available."

    prompt = PROMPT_TEMPLATE.format(
        risk_pct=round(employee_row["risk_score"] * 100, 1),
        shap_drivers_text=shap_text,
        business_unit=bu,
        job_function=employee_row.get("job_function"),
        performance_score=employee_row.get("performance_score"),
        tenure_days=employee_row.get("tenure_days"),
        avg_engagement_score=employee_row.get("avg_engagement_score"),
        avg_satisfaction_score=employee_row.get("avg_satisfaction_score"),
        avg_work_life_balance=employee_row.get("avg_work_life_balance"),
        historical_exits=exits_text
    )

    response = client.chat.completions.create(
        model=config.NIM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=350,
    )
    return response.choices[0].message.content
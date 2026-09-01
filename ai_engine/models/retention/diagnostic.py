from sqlalchemy import text
from database import engine
from openai import OpenAI
import config

def get_department_exit_reasons(department_id):
    """Pulls actual exit reasons from the database for this specific department."""
    query = text("""
        SELECT termination_description 
        FROM v_ai_exit_reason_frequencies
        WHERE department_id = :dept_id
        ORDER BY exit_count DESC
        LIMIT 3;
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"dept_id": department_id}).fetchall()
        return [row[0] for row in result if row[0]]

def generate_manager_report(employee_row):
    """Sends the ML math and conditional historical context to LLaMA."""
    client = OpenAI(base_url=config.NIM_BASE_URL, api_key=config.NIM_API_KEY)
    
    # 1. Format the math from SHAP
    drivers = employee_row.get("top_risk_drivers", [])
    shap_text = "\n".join([f"- {d['feature']}: accounts for {d['impact_pct']}% of elevated risk" for d in drivers])
    
    # 2. Check if department_turnover_rate is actually one of the top drivers
    is_turnover_driver = any(d['feature'] == 'department_turnover_rate' for d in drivers)
    
    # 3. Conditional AI Context Generation
    historical_context_block = ""
    special_instruction = ""
    
    if is_turnover_driver:
        # Failsafe: safely convert to int, default to 0 if missing
        dept_id = int(employee_row.get("department_id", 0))
        if dept_id > 0:
            exit_notes = get_department_exit_reasons(dept_id)
            
            if exit_notes:
                exits_text = "\n".join([f"- {note}" for note in exit_notes])
                historical_context_block = f"\nHistorical Exit Patterns for this Department:\n{exits_text}\n"
                # Strict instruction to tie the exit reasons directly to the turnover driver
                special_instruction = "CRITICAL: When providing the solution for 'department_turnover_rate', you MUST directly address and solve the 'Historical Exit Patterns' listed above."

    # 4. Build the dynamic prompt with a strict structural template
    prompt = f"""You are an HR Predictive Analytics Assistant. 
    An XGBoost ML model calculated a {round(employee_row.get("risk_score", 0) * 100, 1)}% flight risk for this employee.

    Calculated Risk Drivers (XGBoost SHAP):
    {shap_text}
    {historical_context_block}
    
    Task:
    Write an actionable executive diagnostic that maps a specific manager intervention to EACH risk driver listed above.
    
    Format your response exactly like this bulleted list:
    * [Driver Name]: [Brief Explanation] -> [Specific Actionable Solution]
    
    {special_instruction}
    
    Keep the tone highly professional and under 200 words total."""

    response = client.chat.completions.create(
        model=config.NIM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, # Keep this low so it follows instructions strictly
        max_tokens=350,
    )
    return response.choices[0].message.content
"""
Turns a single employee's risk score + raw features into a short
diagnostic explanation, via NVIDIA NIM (OpenAI-compatible endpoint).

This is deliberately called per-employee, on demand -- not in a loop
over every active employee. Running an LLM call for all 3000 rows just
to populate a dashboard would be slow and burns through NIM's free-tier
quota for no reason; the numeric risk_score from predict.py already
covers the bulk dashboard view (KPI card, donut chart). This function is
for the "why is this specific person high-risk" detail view.
"""

from openai import OpenAI
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.NIM_API_KEY:
            raise RuntimeError(
                "NIM_API_KEY is not set. Get a free key at https://build.nvidia.com "
                "and put it in .env as NIM_API_KEY=..."
            )
        _client = OpenAI(base_url=config.NIM_BASE_URL, api_key=config.NIM_API_KEY)
    return _client


PROMPT_TEMPLATE = """You are an HR analytics assistant. An XGBoost model has flagged \
an employee as having a {risk_pct}% probability of leaving the company. \
Given their profile below, write a short diagnostic for their manager.

Employee profile:
- Department: {business_unit}
- Job function: {job_function}
- Performance rating: {performance_score}
- Tenure: {tenure_days} days
- Salary: {salary}
- Average engagement score (1-5): {avg_engagement_score}
- Average satisfaction score (1-5): {avg_satisfaction_score}
- Average work-life balance score (1-5): {avg_work_life_balance}
- Department turnover rate: {department_turnover_rate}%

Respond in two short parts:
1. RISK FACTORS: 2-3 sentences on what in this profile likely drives the risk score. \
If a score is missing (shown as "not available"), don't assume a value -- note that \
survey data is missing as its own factor if relevant.
2. SUGGESTED ACTIONS: 2-3 concrete, specific steps the manager could take.

Keep it under 150 words total. Do not repeat the raw numbers back verbatim -- interpret them."""


def _format_value(v):
    if v is None or (isinstance(v, float) and v != v):  # NaN check without importing math/pandas here
        return "not available"
    return v


def generate_diagnostic(employee_row):
    """employee_row: a pandas Series like the one returned by
    predict.RetentionModel.score_employee() -- must include risk_score
    and the raw feature columns."""
    client = _get_client()

    prompt = PROMPT_TEMPLATE.format(
        risk_pct=round(employee_row["risk_score"] * 100, 1),
        business_unit=_format_value(employee_row.get("business_unit")),
        job_function=_format_value(employee_row.get("job_function")),
        performance_score=_format_value(employee_row.get("performance_score")),
        tenure_days=_format_value(employee_row.get("tenure_days")),
        salary=_format_value(employee_row.get("salary")),
        avg_engagement_score=_format_value(employee_row.get("avg_engagement_score")),
        avg_satisfaction_score=_format_value(employee_row.get("avg_satisfaction_score")),
        avg_work_life_balance=_format_value(employee_row.get("avg_work_life_balance")),
        department_turnover_rate=_format_value(employee_row.get("department_turnover_rate")),
    )

    response = client.chat.completions.create(
        model=config.NIM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=350,
    )
    return response.choices[0].message.content
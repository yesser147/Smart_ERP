import json
from groq import Groq
import config


def generate_budget_proposal(elasticity_df, comparison_chart, sensitivity_curve, worst_depts_analysis):
    client = Groq(api_key=config.GROQ_API_KEY)

    worst_depts_str = json.dumps(worst_depts_analysis, indent=2)

    prompt = f"""You are an AI Chief Financial Officer.
An XGBoost Regression model evaluated department training budget elasticity.

CRITICAL PRIORITY: Target the bottom 3 worst-performing departments with optimal budget increases.

Bottom 3 Departments Analysis & Price Variation Tests:
{worst_depts_str}

Task: Formulate a budget reallocation proposal in JSON format.
Select optimal price variations for these 3 departments that deliver high ROI before diminishing returns set in.

Constraints:
1. Return ONLY a valid JSON object matching this structure:
{{
    "recommended_allocations": [
        {{
            "department_id": 1,
            "department_name": "Name",
            "recommended_budget_increase": 5000,
            "expected_performance_gain": 0.00
        }}
    ],
    "executive_proposal_memo": "Justify your selected price points for the bottom 3 departments.",
    "chart_insights": [
        "Insight 1: Identify diminishing return thresholds.",
        "Insight 2: Strategic takeaway."
    ]
}}"""

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        llm_payload = json.loads(response.choices[0].message.content)
    except Exception as e:
        llm_payload = {
            "recommended_allocations": [],
            "executive_proposal_memo": f"API Error: {str(e)}",
            "chart_insights": ["Review charts manually."]
        }

    # BUG FIXED HERE: the JSON schema above never asks the LLM to return
    # current_budget/current_performance, so the Angular chart's fallback
    # chain (a.current_budget ?? a.base_budget ?? 100000) was hitting the
    # hardcoded $100,000 placeholder for every single department. Never
    # rely on an LLM to accurately echo back a ground-truth number it was
    # never asked to return -- merge the real, deterministic ML numbers
    # in here instead, matched by department_id.
    ground_truth_by_id = {int(d["department_id"]): d for d in worst_depts_analysis}
    for alloc in llm_payload.get("recommended_allocations", []):
        try:
            dept_id = int(alloc.get("department_id"))
        except (TypeError, ValueError):
            continue
        truth = ground_truth_by_id.get(dept_id)
        if truth:
            alloc["current_budget"] = truth["current_budget"]
            alloc["current_performance"] = truth["current_performance"]

    llm_payload["chart_data"] = {
        "department_comparison_bar_chart": comparison_chart,
        "worst_departments_price_tests": worst_depts_analysis
    }

    return llm_payload
import json
from groq import Groq  # Updated import
import config

def generate_budget_proposal(elasticity_df, comparison_chart, sensitivity_curve):
    """Sends elasticity calculations AND chart data to Groq for full synthesis and visual deduction."""
    # Initialize native Groq client
    client = Groq(api_key=config.GROQ_API_KEY)

    top_departments = elasticity_df.head(3)
    metrics_summary = ""
    for _, row in top_departments.iterrows():
        dept_name = row.get('department_type') or f"Dept #{int(row['department_id'])}"
        curr_budget = float(row['training_budget'])
        gain = float(row['performance_gain'])
        metrics_summary += f"- {dept_name} (Current Spend: ${curr_budget:,.2f}): +$5,000 yields +{gain:.3f} gain.\n"

    # Convert the curve data to a string so the LLM can read the trends
    curve_data_str = json.dumps(sensitivity_curve)

    prompt = f"""You are an AI Chief Financial Officer.
An XGBoost Regression model evaluated department training budget elasticity.

Top Investment Opportunities ($5k increment):
{metrics_summary}

Simulated Budget Sensitivity Curve (0 to $20k):
{curve_data_str}

Task: Formulate a budget reallocation proposal in JSON format.

Constraints:
1. Return ONLY a valid JSON object.
2. Must match this exact structure:
{{
    "recommended_allocations": [
        {{
            "department_id": 1,
            "department_name": "Name",
            "recommended_budget_increase": 5000,
            "expected_performance_gain": 0.00
        }}
    ],
    "executive_proposal_memo": "Write a concise executive memo justifying these choices.",
    "chart_insights": [
        "Insight 1: Identify at what dollar amount the returns start to diminish based on the curve data.",
        "Insight 2: Compare the top two departments from the curve data."
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

        llm_payload = json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"\n[API Warning] Budget Proposal Generation Failed: {str(e)}")
        llm_payload = {
            "recommended_allocations": [],
            "executive_proposal_memo": f"Unable to generate proposal due to API error: {str(e)}",
            "chart_insights": ["Review sensitivity charts manually."]
        }

    # Attach the frontend graph data directly to the payload
    llm_payload["chart_data"] = {
        "department_comparison_bar_chart": comparison_chart,
        "budget_sensitivity_line_chart": sensitivity_curve
    }

    return llm_payload
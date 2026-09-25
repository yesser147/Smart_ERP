import json
import logging
import config
from models.recruitment.llm_client import generate_json

log = logging.getLogger(__name__)

METRICS_PATH = config.BUDGET_METRICS_PATH


def _clean(value):
    """Keep only real, non-empty strings."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _load_model_quality():
    """Data-driven reliability level, computed from the cross-validation
    metrics saved by train.py."""
    try:
        with open(METRICS_PATH, encoding='utf-8') as f:
            m = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"level": "unknown", "cv_r2": None, "cv_mae": None,
                "n_rows": None, "n_rows_total": None, "min_headcount": None}

    r2 = m.get("cv_r2")
    if r2 is None or r2 < 0.05:
        level = "insufficient"
    elif r2 < 0.25:
        level = "low"
    else:
        level = "acceptable"

    return {
        "level": level,
        "cv_r2": r2,
        "cv_mae": m.get("cv_mae"),
        "n_rows": m.get("n_rows"),
        "n_rows_total": m.get("n_rows_total"),
        "min_headcount": m.get("min_headcount"),
    }


def generate_budget_proposal(elasticity_df, comparison_chart, sensitivity_curve, worst_depts_analysis):
    quality = _load_model_quality()
    analysis_str = json.dumps(worst_depts_analysis, indent=2)
    quality_str = json.dumps(quality)

    prompt = f"""You are an AI Chief Financial Officer.
An XGBoost Regression model evaluated department training budget elasticity.

MODEL QUALITY (cross-validated on unseen departments): {quality_str}
- cv_r2 near 0 means the model cannot predict performance better than guessing the average.
- If level is "insufficient" or "low", the memo MUST clearly say that the available data is not
  enough for reliable predictions and that the figures are illustrative only.

You are given 6 departments: the 3 TOP performers (group "top") and the 3 BOTTOM performers (group "bottom"),
ranked by current predicted performance. For each one, the model already computed the OPTIMAL training budget
(the peak of its performance/budget curve). "budget_change" is optimal_budget minus current_budget and can be
negative, which means the model predicts higher performance with a LOWER budget.

Analysis:
{analysis_str}

Task: Write an executive memo and strategic insights that explain these optimal budgets.
Do NOT change or invent any number. Mention departments where the model recommends a reduction.

Return ONLY a valid JSON object matching this structure:
{{
    "executive_proposal_memo": "Explain the optimal budgets and the reliability of the predictions.",
    "chart_insights": [
        "Insight 1: Identify diminishing return thresholds.",
        "Insight 2: Strategic takeaway."
    ]
}}"""

    try:
        llm_payload = generate_json(prompt, temperature=0.2, max_tokens=1500)
    except Exception as e:
        log.warning("Budget memo generation failed: %s", e)
        llm_payload = {
            "executive_proposal_memo": f"API Error: {str(e)}",
            "chart_insights": ["Review charts manually."]
        }

    meta_by_id = {}
    if elasticity_df is not None and not elasticity_df.empty:
        for _, row in elasticity_df.iterrows():
            meta_by_id[int(row["department_id"])] = {
                "division_description": _clean(row.get("division_description")),
                "department_type": _clean(row.get("department_type")),
                "business_unit": _clean(row.get("business_unit")),
            }

    allocations = []
    for d in worst_depts_analysis:
        dept_id = int(d["department_id"])
        allocations.append({
            "department_id": dept_id,
            "department_name": d["department_name"],
            "group": d["group"],
            "current_budget": d["current_budget"],
            "current_performance": d["current_performance"],
            "optimal_budget": d["optimal_budget"],
            "recommended_budget_increase": d["budget_change"],  # signed change vs current
            "predicted_performance": d["optimal_performance"],
            "expected_performance_gain": d["performance_gain"],
            **meta_by_id.get(dept_id, {
                "division_description": None,
                "department_type": None,
                "business_unit": None,
            }),
        })

    llm_payload["recommended_allocations"] = allocations
    llm_payload["model_quality"] = quality
    llm_payload["chart_data"] = {
        "department_comparison_bar_chart": comparison_chart,
        "worst_departments_price_tests": worst_depts_analysis
    }

    return llm_payload
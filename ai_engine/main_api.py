import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from models.recruitment.cv_processing import process_applicant_cv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.nl_assistant.nl_query_assistant import HRQueryAssistant
from models.budget_advisor.predict import BudgetPrescriptor
from models.budget_advisor.advise import generate_budget_proposal
from models.retention.predict import RetentionPredictor
from models.retention.diagnostic import generate_macro_retention_strategy
from models.recruitment.matcher import match_candidates_to_job  # NEW

app = FastAPI(title="SmartERP AI Services API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

nl_assistant = HRQueryAssistant()
RISK_THRESHOLD = 0.70


class ChatRequest(BaseModel):
    question: str


class SimulateBudgetRequest(BaseModel):
    department_id: int
    new_budget: float


@app.post("/api/ai/chat")
async def ask_assistant(request: ChatRequest):
    try:
        result = nl_assistant.ask(request.question)
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/budget-advisor")
def get_budget_advice():
    try:
        prescriptor = BudgetPrescriptor()
        elasticity_df, comparison_chart, sensitivity_curve, worst_dept_analysis = prescriptor.calculate_elasticity_and_charts()

        if elasticity_df.empty:
            raise HTTPException(status_code=404, detail="No data available for elasticity analysis.")

        payload = generate_budget_proposal(
            elasticity_df, comparison_chart, sensitivity_curve, worst_dept_analysis
        )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to generate budget advice: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.get("/api/ai/budget-advisor/departments")
def get_budget_departments():
    try:
        prescriptor = BudgetPrescriptor()
        baselines = prescriptor.get_department_baselines()
        if not baselines:
            raise HTTPException(status_code=404, detail="No department data available.")
        return baselines
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to load department baselines: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.post("/api/ai/budget-advisor/simulate")
def simulate_budget(request: SimulateBudgetRequest):
    try:
        prescriptor = BudgetPrescriptor()
        result = prescriptor.simulate_single_department(request.department_id, request.new_budget)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No department found with id {request.department_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to simulate budget change: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.get("/api/ai/retention-macro")
async def get_retention_strategy():
    try:
        predictor = RetentionPredictor()
        scored_employees = predictor.analyze_active_employees()

        if scored_employees.empty:
            raise HTTPException(status_code=404, detail="No active employees found.")

        total_active = len(scored_employees)
        high_risk_df = scored_employees[scored_employees["risk_score"] >= RISK_THRESHOLD]

        if high_risk_df.empty:
            top_10 = max(1, int(total_active * 0.10))
            high_risk_df = scored_employees.sort_values(by="risk_score", ascending=False).head(top_10)

        macro_strategy = generate_macro_retention_strategy(high_risk_df, total_active, threshold=RISK_THRESHOLD)
        return macro_strategy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/retention-risk-scores")
def get_retention_risk_scores(threshold: float = RISK_THRESHOLD):
    try:
        predictor = RetentionPredictor()
        scored = predictor.analyze_active_employees()
        if scored.empty:
            return {"high_risk_count": 0, "total_active": 0}
        total_active = len(scored)
        high_risk_count = int((scored["risk_score"] >= threshold).sum())
        return {"high_risk_count": high_risk_count, "total_active": total_active}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: Recruitment candidate matching ---

@app.get("/api/ai/recruitment/match/{job_id}")
def get_candidate_matches(job_id: int, top_k: int = 10, recompute_all: bool = False):
    try:
        result = match_candidates_to_job(job_id, top_k, recompute_all)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No job posting found with id {job_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.post("/api/ai/recruitment/process-cv/{applicant_id}")
def process_cv(applicant_id: int):
    result = process_applicant_cv(applicant_id)
    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["message"])
    return result

if __name__ == "__main__":
    print("Starting AI Services API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
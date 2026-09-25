import os
import sys
import logging
import math
import threading
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

import config
from database import engine
from security import require_admin, require_hr_user
from models.nl_assistant.nl_query_assistant import HRQueryAssistant
from models.budget_advisor.predict import BudgetPrescriptor
from models.budget_advisor.advise import generate_budget_proposal
from models.retention.predict import RetentionPredictor
from models.retention.diagnostic import generate_macro_retention_strategy, _load_model_quality
from models.retention.survival import retention_curves
from models.recruitment.cv_processing import process_applicant_cv
from models.recruitment.matcher import match_candidates_to_job
from models.recruitment.applicant_chat import get_chat_history, reset_chat, stream_chat_message, ChatError
from models.recruitment.recruiter_tools import search_cvs, job_description, interview_questions
from models.recruitment.llm_client import LLMUnavailable
from models import model_admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ai_engine")


def _json_safe(value):
    """NaN / infinity (pandas' missing values) -> null, recursively."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


class SafeJSONResponse(JSONResponse):
    """A missing value somewhere in a result must never turn into a 500."""
    def render(self, content) -> bytes:
        return super().render(_json_safe(jsonable_encoder(content)))


# Every route requires the backend's login token with an HR role.
# The interactive docs are only served when API_DOCS=true.
docs = os.environ.get("API_DOCS", "false").lower() == "true"
app = FastAPI(
    title="Nexus ERP AI Services",
    dependencies=[Depends(require_hr_user)],
    default_response_class=SafeJSONResponse,
    docs_url="/docs" if docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,          # the token travels in a header, not a cookie
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

nl_assistant = HRQueryAssistant()
DEFAULT_RISK_THRESHOLD = 0.5


# ---------------------------------------------------------------- shared state
# Models are loaded once (not on every request). Retention scoring
# (XGBoost + SHAP on every active employee) and the LLM strategy built on it
# are cached for RETENTION_CACHE_SECONDS.

_lock = threading.Lock()
_state = {"retention": None, "budget": None}
_scored_cache = {"at": 0.0, "df": None}
_strategy_cache = {"at": 0.0, "value": None}


def get_retention_predictor() -> RetentionPredictor:
    with _lock:
        if _state["retention"] is None:
            _state["retention"] = RetentionPredictor()
        return _state["retention"]


def get_budget_prescriptor() -> BudgetPrescriptor:
    with _lock:
        if _state["budget"] is None:
            _state["budget"] = BudgetPrescriptor()
        return _state["budget"]


def reset_models():
    """After a retraining: reload the models and drop every cached result."""
    with _lock:
        _state["retention"] = _state["budget"] = None
        _scored_cache.update(df=None, at=0.0)
        _strategy_cache.update(value=None, at=0.0)


def _fresh(cache_time: float) -> bool:
    return time.time() - cache_time < config.RETENTION_CACHE_SECONDS


def scored_active_employees():
    if _scored_cache["df"] is None or not _fresh(_scored_cache["at"]):
        _scored_cache["df"] = get_retention_predictor().analyze_active_employees()
        _scored_cache["at"] = time.time()
    return _scored_cache["df"]


def risk_threshold() -> float:
    """'High risk' cut-off learned at training time (best F1 on out-of-fold
    predictions, see models/retention/train.py); 0.5 for older models."""
    return _load_model_quality().get("risk_threshold") or DEFAULT_RISK_THRESHOLD


def _internal_error(what: str):
    log.exception(what)
    raise HTTPException(status_code=500, detail="An internal server error occurred.")


# ---------------------------------------------------------------- requests

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = None


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class SimulateBudgetRequest(BaseModel):
    department_id: int
    new_budget: float = Field(ge=0)


class JobDescriptionRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    department: str | None = None
    required_experience_years: float | None = None


# ---------------------------------------------------------------- HR chatbot

def _log_question(user_email: str | None, question: str, answer: str | None, elapsed_ms: int):
    """Saves the question in ai_query_logs (popular questions, usage)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO ai_query_logs (id, user_id, prompt, response, execution_time_ms, created_at, created_by)
                SELECT gen_random_uuid(), u.id, :q, :a, :ms, CURRENT_TIMESTAMP, :email
                FROM users u WHERE u.email = :email
            """), {"q": question, "a": answer, "ms": elapsed_ms, "email": user_email})
    except Exception as e:           # logging must never break the answer
        log.warning("Could not log the chatbot question: %s", e)


@app.post("/api/ai/chat")
def ask_assistant(request: ChatRequest, user: dict = Depends(require_hr_user)):
    started = time.time()
    # one memory per conversation (the widget sends its own id), per user by default
    conversation_id = request.conversation_id or f"user:{user.get('sub', 'anonymous')}"
    result = nl_assistant.ask(request.question, conversation_id=conversation_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    _log_question(user.get("sub"), request.question, result.get("summary"), int((time.time() - started) * 1000))
    return result


@app.get("/api/ai/chat/popular")
def popular_questions(limit: int = 6):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT MIN(prompt) AS prompt, COUNT(*) AS asked
            FROM ai_query_logs
            WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '90 days'
            GROUP BY LOWER(TRIM(prompt))
            ORDER BY asked DESC, MAX(created_at) DESC
            LIMIT :limit
        """), {"limit": max(1, min(limit, 20))}).fetchall()
    return [{"question": r.prompt, "asked": int(r.asked)} for r in rows]


# ---------------------------------------------------------------- budget advisor

@app.get("/api/ai/budget-advisor")
def get_budget_advice():
    try:
        elasticity_df, comparison_chart, sensitivity_curve, extremes = \
            get_budget_prescriptor().calculate_elasticity_and_charts()
        if elasticity_df.empty:
            raise HTTPException(status_code=404, detail="No data available for the budget analysis.")
        return generate_budget_proposal(elasticity_df, comparison_chart, sensitivity_curve, extremes)
    except HTTPException:
        raise
    except Exception:
        _internal_error("Failed to generate budget advice")


@app.get("/api/ai/budget-advisor/departments")
def get_budget_departments():
    try:
        baselines = get_budget_prescriptor().get_department_baselines()
        if not baselines:
            raise HTTPException(status_code=404, detail="No team data available.")
        return baselines
    except HTTPException:
        raise
    except Exception:
        _internal_error("Failed to load team baselines")


@app.post("/api/ai/budget-advisor/simulate")
def simulate_budget(request: SimulateBudgetRequest):
    try:
        result = get_budget_prescriptor().simulate_single_department(request.department_id, request.new_budget)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No team with id {request.department_id}")
        return result
    except HTTPException:
        raise
    except Exception:
        _internal_error("Failed to simulate a budget change")


# ---------------------------------------------------------------- retention

@app.get("/api/ai/retention-macro")
def get_retention_strategy():
    try:
        if _strategy_cache["value"] is not None and _fresh(_strategy_cache["at"]):
            return _strategy_cache["value"]

        scored = scored_active_employees()
        if scored.empty:
            raise HTTPException(status_code=404, detail="No active employees found.")

        threshold = risk_threshold()
        high_risk = scored[scored["risk_score"] >= threshold]
        if high_risk.empty:
            high_risk = scored.sort_values(by="risk_score", ascending=False).head(max(1, int(len(scored) * 0.10)))

        strategy = generate_macro_retention_strategy(high_risk, len(scored), threshold=threshold)
        _strategy_cache.update(value=strategy, at=time.time())
        return strategy
    except HTTPException:
        raise
    except Exception:
        _internal_error("Failed to generate the retention strategy")


@app.get("/api/ai/retention-risk-scores")
def get_retention_risk_scores(threshold: float | None = None):
    """ML only (no LLM): cheap enough for the dashboard KPIs."""
    try:
        scored = scored_active_employees()
        quality = _load_model_quality()
        threshold = threshold if threshold is not None else risk_threshold()
        if scored.empty:
            return {"high_risk_count": 0, "total_active": 0, "model_quality": quality}
        return {
            "high_risk_count": int((scored["risk_score"] >= threshold).sum()),
            "total_active": len(scored),
            "model_quality": quality,
        }
    except Exception:
        _internal_error("Failed to compute retention risk scores")


@app.get("/api/ai/retention/employee/{employee_id}")
def get_employee_risk(employee_id: int):
    """Risk score and its main drivers (SHAP) for one active employee."""
    try:
        scored = scored_active_employees()
        row = scored[scored["employee_id"] == employee_id]
        if row.empty:
            raise HTTPException(status_code=404, detail="No risk score: the employee is not active.")
        r = row.iloc[0]
        threshold = risk_threshold()
        rank = int((scored["risk_score"] > r["risk_score"]).sum()) + 1
        return {
            "employee_id": employee_id,
            "risk_score": round(float(r["risk_score"]), 3),
            "threshold": threshold,
            "high_risk": bool(r["risk_score"] >= threshold),
            "rank": rank,
            "total_active": len(scored),
            "drivers": r["top_risk_drivers"],
            "model_quality": _load_model_quality(),
        }
    except HTTPException:
        raise
    except Exception:
        _internal_error("Failed to score the employee")


@app.get("/api/ai/retention/at-risk")
def get_at_risk_employees(limit: int = 15):
    """The active employees with the highest risk score, with their main drivers."""
    try:
        scored = scored_active_employees()
        if scored.empty:
            return []
        top = scored.sort_values("risk_score", ascending=False).head(max(1, min(limit, 100)))
        ids = [int(i) for i in top["employee_id"]]
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT e.employee_id, e.first_name, e.last_name, e.title, d.department_type, d.division_description
                FROM employees e LEFT JOIN departments d ON d.department_id = e.department_id
                WHERE e.employee_id = ANY(:ids)
            """), {"ids": ids}).fetchall()
        info = {r.employee_id: r for r in rows}
        threshold = risk_threshold()
        result = []
        for r in top.itertuples():
            e = info.get(int(r.employee_id))
            if e is None:
                continue
            result.append({
                "employee_id": int(r.employee_id),
                "name": f"{e.first_name} {e.last_name}",
                "title": e.title,
                "department": e.department_type,
                "team": e.division_description,
                "risk_score": round(float(r.risk_score), 3),
                "high_risk": bool(r.risk_score >= threshold),
                "drivers": r.top_risk_drivers,
            })
        return result
    except Exception:
        _internal_error("Failed to list the employees at risk")


@app.get("/api/ai/retention/survival")
def get_retention_curves():
    try:
        return retention_curves()
    except Exception:
        _internal_error("Failed to compute the retention curves")


# ---------------------------------------------------------------- recruitment

@app.get("/api/ai/recruitment/match/{job_id}")
def get_candidate_matches(job_id: int, top_k: int = 10, recompute_all: bool = False):
    try:
        result = match_candidates_to_job(job_id, top_k, recompute_all)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No job posting with id {job_id}")
        return result
    except HTTPException:
        raise
    except Exception:
        _internal_error(f"Candidate matching failed for job {job_id}")


@app.post("/api/ai/recruitment/process-cv/{applicant_id}")
def process_cv(applicant_id: int):
    result = process_applicant_cv(applicant_id)
    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@app.get("/api/ai/recruitment/search")
def search_candidates(q: str, limit: int = 20):
    if len(q.strip()) < 3:
        raise HTTPException(status_code=400, detail="Type at least 3 characters.")
    try:
        return search_cvs(q.strip(), limit)
    except Exception:
        _internal_error("CV search failed")


@app.post("/api/ai/recruitment/job-description")
def generate_job_description(request: JobDescriptionRequest):
    try:
        return job_description(request.title, request.department, request.required_experience_years)
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=f"AI unavailable: {e}")
    except Exception:
        _internal_error("Job description generation failed")


@app.post("/api/ai/recruitment/interview-questions/{applicant_id}/{job_id}")
def generate_interview_questions(applicant_id: int, job_id: int):
    try:
        result = interview_questions(applicant_id, job_id)
        if result is None:
            raise HTTPException(status_code=422, detail="Job not found or the CV has not been processed yet.")
        return result
    except HTTPException:
        raise
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=f"AI unavailable: {e}")
    except Exception:
        _internal_error("Interview question generation failed")


@app.post("/api/ai/recruitment/chat/{applicant_id}/{job_id}/stream")
def chat_about_applicant_stream(applicant_id: int, job_id: int, request: ChatMessageRequest):
    try:
        generator = stream_chat_message(applicant_id, job_id, request.message)
    except ChatError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=f"AI unavailable: {e}")
    return StreamingResponse(
        generator,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/ai/recruitment/chat/{applicant_id}/{job_id}/history")
def get_applicant_chat_history(applicant_id: int, job_id: int):
    return {"messages": get_chat_history(applicant_id, job_id)}


@app.delete("/api/ai/recruitment/chat/{applicant_id}/{job_id}")
def reset_applicant_chat(applicant_id: int, job_id: int):
    reset_chat(applicant_id, job_id)
    return {"status": "reset"}


# ---------------------------------------------------------------- model monitoring

@app.get("/api/ai/models")
def models_status():
    return model_admin.status()


@app.post("/api/ai/models/retrain")
def retrain_models(_: dict = Depends(require_admin)):
    try:
        result = model_admin.retrain()
        reset_models()
        return result
    except model_admin.RetrainBusy as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception:
        _internal_error("Retraining failed")


if __name__ == "__main__":
    log.info("Starting the AI API on http://%s:%s", config.API_HOST, config.API_PORT)
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)

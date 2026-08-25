import math
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from models.retention import predict as retention_predict
from models.retention import diagnostic as retention_diagnostic
from models.retention.train import train as retention_train
from models.retention.features import fetch_raw
from models.retention.schemas import RiskScore, Diagnostic, TrainResult

router = APIRouter(prefix="/ai/retention", tags=["retention"])


def _clean_float(v):
    """NaN isn't valid JSON -- turn it into None so FastAPI doesn't choke
    on employees with missing survey scores."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


@router.get("/risk-scores", response_model=list[RiskScore])
def get_risk_scores():
    """Bulk numeric risk scores for every active employee. Cheap, no LLM
    calls -- this is what feeds the dashboard's High Risk KPI / donut."""
    try:
        model = retention_predict.get_model()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    scored = model.score_all_active()
    return [
        RiskScore(
            employee_id=row.employee_id,
            department_id=_clean_float(row.department_id),
            business_unit=row.business_unit,
            risk_score=round(float(row.risk_score), 4),
        )
        for row in scored.itertuples()
    ]


@router.get("/employees/{employee_id}/diagnostic", response_model=Diagnostic)
def get_employee_diagnostic(employee_id: str):
    """On-demand: scores one employee AND generates an LLM explanation.
    Call this from a 'view details' action on a specific employee, not
    in a loop."""
    try:
        model = retention_predict.get_model()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    row = model.score_employee(employee_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No active employee found with id {employee_id}")

    try:
        text = retention_diagnostic.generate_diagnostic(row)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return Diagnostic(
        employee_id=employee_id,
        risk_score=round(float(row["risk_score"]), 4),
        diagnostic_text=text,
    )


@router.post("/train", response_model=TrainResult)
async def trigger_training():
    """Retrains the model from whatever's currently in Postgres. Runs in
    a threadpool since it's a blocking, CPU-bound call -- don't want it
    freezing the event loop for other requests while it fits.

    No auth on this yet -- fine for a school project, but lock this down
    (admin-only) before this is ever public."""
    raw = await run_in_threadpool(fetch_raw, only_active=False)
    n = len(raw)
    await run_in_threadpool(retention_train)
    retention_predict._instance = None  # force reload of the new model on next request
    return TrainResult(status="trained", employees_trained_on=n)
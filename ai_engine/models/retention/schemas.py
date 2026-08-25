from typing import Optional
from pydantic import BaseModel


class RiskScore(BaseModel):
    employee_id: str
    department_id: Optional[int] = None
    business_unit: Optional[str] = None
    risk_score: float


class Diagnostic(BaseModel):
    employee_id: str
    risk_score: float
    diagnostic_text: str


class TrainResult(BaseModel):
    status: str
    employees_trained_on: int
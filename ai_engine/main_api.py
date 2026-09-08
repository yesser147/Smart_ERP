import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Imports from your ML Models ---
from models.nl_assistant.nl_query_assistant import HRQueryAssistant
from models.budget_advisor.predict import BudgetPrescriptor
from models.budget_advisor.advise import generate_budget_proposal
from models.retention.predict import RetentionPredictor
from models.retention.diagnostic import generate_macro_retention_strategy

app = FastAPI(title="SmartERP AI Services API")

# Allow frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to your frontend URL in production (e.g., "http://localhost:4200")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the NL Assistant once to keep it warm
nl_assistant = HRQueryAssistant()
RISK_THRESHOLD = 0.70

# --- Pydantic Schemas ---
class ChatRequest(BaseModel):
    question: str

# --- API Endpoints ---

@app.post("/api/ai/chat")
async def ask_assistant(request: ChatRequest):
    """Natural Language HR/Finance Assistant"""
    try:
        result = nl_assistant.ask(request.question)
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/budget-advisor")
def get_budget_advice():
    """Generates prescriptive budget allocations"""
    try:
        prescriptor = BudgetPrescriptor()
        
        # FIX: Unpack all 4 returned values
        elasticity_df, comparison_chart, sensitivity_curve, worst_dept_analysis = prescriptor.calculate_elasticity_and_charts()
        
        if elasticity_df.empty:
            raise HTTPException(status_code=404, detail="No data available for elasticity analysis.")
            
        # FIX: Pass the 4th parameter to the generator
        payload = generate_budget_proposal(
            elasticity_df, 
            comparison_chart, 
            sensitivity_curve, 
            worst_dept_analysis
        )
        return payload
        
    except HTTPException:
        raise
        
    except Exception as e:
        logging.error(f"Failed to generate budget advice: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/api/ai/retention-macro")
async def get_retention_strategy():
    """Generates macro retention strategy based on flight risks"""
    try:
        predictor = RetentionPredictor()
        scored_employees = predictor.analyze_active_employees()
        
        if scored_employees.empty:
            raise HTTPException(status_code=404, detail="No active employees found.")
            
        total_active = len(scored_employees)
        high_risk_df = scored_employees[scored_employees["risk_score"] >= RISK_THRESHOLD]
        
        # Fallback to top 10% if no one exceeds threshold
        if high_risk_df.empty:
            top_10 = max(1, int(total_active * 0.10))
            high_risk_df = scored_employees.sort_values(by="risk_score", ascending=False).head(top_10)

        macro_strategy = generate_macro_retention_strategy(high_risk_df, total_active, threshold=RISK_THRESHOLD)
        return macro_strategy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting AI Services API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI
from routers import retention

app = FastAPI(
    title="Smart ERP Core -- AI Engine",
    description="Predictive retention (Service 1). Budget advisor and NL "
                "assistant (Services 2-3) not implemented yet.",
    version="0.1.0",
)

app.include_router(retention.router)


@app.get("/health")
def health():
    return {"status": "ok"}
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv(override=True)

# Database credentials (matching your working ETL defaults)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5050")  # Docker host port
DB_NAME = os.environ.get("DB_NAME", "smart_erp")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", "postgres"))

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# NVIDIA NIM Config
NIM_API_KEY = os.environ.get("NIM_API_KEY", "")
NIM_BASE_URL = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_MODEL = os.environ.get("NIM_MODEL", "meta/llama-3.3-70b-instruct")

# Artifact Paths
ARTIFACT_DIR = os.environ.get("AI_ARTIFACT_DIR", "./artifacts")
RETENTION_MODEL_PATH = os.path.join(ARTIFACT_DIR, "retention_model.json")
RETENTION_SCHEMA_PATH = os.path.join(ARTIFACT_DIR, "retention_feature_schema.joblib")

# Model Training Parameters
CHURN_STATUSES = ["Terminated"]
CATEGORICAL_FEATURES = ["business_unit", "job_function", "performance_score", "gender"]
NUMERIC_FEATURES = [
    "salary",
    "tenure_days",
    "avg_engagement_score",
    "avg_satisfaction_score",
    "avg_work_life_balance",
    "department_turnover_rate",
]
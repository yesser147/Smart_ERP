import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# .env next to this file, whatever the current folder is. Real environment
# variables win over .env (standard behaviour; handy for tests and servers).
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

# -------------------------------------------------------------------
# Database Configuration
# -------------------------------------------------------------------

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "smart_erp")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", ""))

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -------------------------------------------------------------------
# AI Query Assistant Database (read-only role, created by the backend's
# R__create_bi_views.sql)
# -------------------------------------------------------------------

AI_DB_USER = os.environ.get("AI_DB_USER", "ai_readonly_user")
AI_DB_PASSWORD = quote_plus(os.environ.get("AI_DB_PASSWORD", ""))

AI_DATABASE_URL = (
    f"postgresql+psycopg2://{AI_DB_USER}:{AI_DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Generated SQL is cut off after this many milliseconds
AI_STATEMENT_TIMEOUT_MS = int(os.environ.get("AI_STATEMENT_TIMEOUT_MS", "10000"))

# -------------------------------------------------------------------
# LLMs (all calls go through models/recruitment/llm_client.py)
# -------------------------------------------------------------------

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")        # groq | ollama
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

# -------------------------------------------------------------------
# Security / API
# -------------------------------------------------------------------

# Same value as JWT_SECRET in backend/.env: used to verify the login token
JWT_SECRET = os.environ.get("JWT_SECRET", "")
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",") if o.strip()]
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8000"))

# -------------------------------------------------------------------
# MinIO (private bucket holding the CV PDFs)
# -------------------------------------------------------------------

# Where THIS process reaches MinIO. Stored CV URLs may name another host
# (localhost:9000 from the ETL, minio:9000 from the backend container):
# only their path is used, see storage.py.
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")

# -------------------------------------------------------------------
# Artifact Paths
# -------------------------------------------------------------------

ARTIFACT_DIR = os.environ.get("AI_ARTIFACT_DIR", os.path.join(BASE_DIR, "artifacts"))

RETENTION_MODEL_PATH = os.path.join(ARTIFACT_DIR, "retention_model.json")
RETENTION_SCHEMA_PATH = os.path.join(ARTIFACT_DIR, "retention_feature_schema.joblib")
RETENTION_METRICS_PATH = os.path.join(ARTIFACT_DIR, "retention_metrics.json")

BUDGET_MODEL_DIR = os.environ.get(
    "AI_BUDGET_MODEL_DIR", os.path.join(BASE_DIR, "models", "budget", "saved_models")
)
BUDGET_MODEL_PATH = os.path.join(BUDGET_MODEL_DIR, "budget_xgboost.pkl")
BUDGET_METRICS_PATH = os.path.join(BUDGET_MODEL_DIR, "budget_metrics.json")

# -------------------------------------------------------------------
# Model Training Parameters
# -------------------------------------------------------------------

# Features of the attrition model (columns of v_ai_retention_features).
# Protected attributes (gender, age, marital status) are deliberately NOT
# features: they must not drive an attrition score.
CATEGORICAL_FEATURES = [
    "department_type",
    "job_function",          # job role
    "business_travel",
    "performance_score",
]

NUMERIC_FEATURES = [
    "salary",
    "tenure_days",
    "job_level",
    "overtime",
    "distance_from_home",
    "total_working_years",
    "num_companies_worked",
    "years_in_current_role",
    "years_since_last_promotion",
    "years_with_curr_manager",
    "stock_option_level",
    "percent_salary_hike",
    "environment_satisfaction",
    "relationship_satisfaction",
    "training_times_last_year",
    "avg_engagement_score",
    "avg_satisfaction_score",
    "avg_work_life_balance",
]

CHURN_STATUSES = ["Terminated"]

MIN_CATEGORY_COUNT = 30

# Retention results (XGBoost + SHAP + LLM strategy) are cached this long
RETENTION_CACHE_SECONDS = int(os.environ.get("RETENTION_CACHE_SECONDS", "600"))

# -------------------------------------------------------------------
# Candidate matching
# -------------------------------------------------------------------

# at most this many candidates per search are judged by the LLM (the best
# ones by the cheap signals); the others keep their pre-screen score
MATCH_LLM_MAX = int(os.environ.get("MATCH_LLM_MAX", "25"))

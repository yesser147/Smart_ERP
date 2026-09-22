import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv(override=True)

# -------------------------------------------------------------------
# Database Configuration
# -------------------------------------------------------------------

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5050")
DB_NAME = os.environ.get("DB_NAME", "smart_erp")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", "postgres"))

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -------------------------------------------------------------------
# AI Query Assistant Database
# -------------------------------------------------------------------

AI_DB_USER = os.environ.get("AI_DB_USER", "ai_readonly_user")
AI_DB_PASSWORD = quote_plus(
    os.environ.get("AI_DB_PASSWORD", "SecurePassword123!")
)

AI_DATABASE_URL = (
    f"postgresql+psycopg2://{AI_DB_USER}:{AI_DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -------------------------------------------------------------------
# NVIDIA NIM / Groq Configuration
# -------------------------------------------------------------------

NIM_API_KEY = os.environ.get("NIM_API_KEY")
NIM_BASE_URL = os.environ.get(
    "NIM_BASE_URL",
    "https://api.groq.com/openai/v1"
)
NIM_MODEL = os.environ.get(
    "NIM_MODEL",
    "llama-3.3-70b-versatile"
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

# -------------------------------------------------------------------
# Artifact Paths
# -------------------------------------------------------------------

ARTIFACT_DIR = os.environ.get(
    "AI_ARTIFACT_DIR",
    "./artifacts"
)

RETENTION_MODEL_PATH = os.path.join(
    ARTIFACT_DIR,
    "retention_model.json"
)

RETENTION_SCHEMA_PATH = os.path.join(
    ARTIFACT_DIR,
    "retention_feature_schema.joblib"
)

# -------------------------------------------------------------------
# Model Training Parameters
# -------------------------------------------------------------------

CATEGORICAL_FEATURES = [
    "division_description",
    "job_function",
    "performance_score",
    "gender",
]

NUMERIC_FEATURES = [
    "salary",
    "tenure_days",
    "avg_engagement_score",
    "avg_satisfaction_score",
    "avg_work_life_balance",
]

CHURN_STATUSES = ["Terminated"]

MIN_CATEGORY_COUNT = 30

# -------------------------------------------------------------------
# Gemini
# -------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
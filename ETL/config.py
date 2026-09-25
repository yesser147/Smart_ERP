"""
Central configuration for the Smart ERP Core ETL pipeline.
Change values here instead of hunting through the pipeline code.

Data sources (put them in sample_data/, git-ignored):
  - IBM HR Analytics Employee Attrition & Performance (1,470 employees)
    https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
    Simulated by IBM data scientists with REALISTIC relationships between the
    variables (overtime, satisfaction, promotions, pay... really drive attrition).
  - Kaggle Resume Dataset (2,484 real resumes, text + PDF, 24 categories)
    https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_DIR = os.environ.get("ETL_INPUT_DIR", os.path.join(BASE_DIR, "sample_data"))
OUTPUT_DIR = os.environ.get("ETL_OUTPUT_DIR", os.path.join(BASE_DIR, "output"))
REPORT_DIR = os.environ.get("ETL_REPORT_DIR", os.path.join(BASE_DIR, "reports"))

# The backend's Flyway migrations: the ETL builds its tables from these files
# (see load.apply_schema), so there is only one schema definition.
MIGRATIONS_DIR = os.environ.get(
    "ETL_MIGRATIONS_DIR",
    os.path.join(BASE_DIR, "..", "backend", "src", "main", "resources", "db", "migration"),
)

# Accepted file names (first one found wins)
EMPLOYEE_FILES = ["WA_Fn-UseC_-HR-Employee-Attrition.csv", "emp_attrition.csv", "ibm_hr_attrition.csv"]
RESUME_CSV = os.environ.get("RESUME_CSV", os.path.join(INPUT_DIR, "Resume", "Resume.csv"))
RESUME_PDF_DIR = os.environ.get("RESUME_PDF_DIR", os.path.join(INPUT_DIR, "data", "data"))

# ---------------------------------------------------------------------------
# Reproducibility and time
# ---------------------------------------------------------------------------
SEED = 42
# The IBM file is a snapshot without dates. Dates (hire, exit, survey,
# training, recruitment) are placed relative to this day. Default: today.
SNAPSHOT_DATE = os.environ.get("ETL_SNAPSHOT_DATE")  # "YYYY-MM-DD" or None

COMPANY_DOMAIN = "nexuserp.com"
COMPANY_LOCATION = "Head Office"

# ---------------------------------------------------------------------------
# Organisation
# ---------------------------------------------------------------------------
DEPARTMENT_CODES = {
    "Research & Development": "RD",
    "Sales": "SL",
    "Human Resources": "HR",
}
ROLE_CODES = {
    "Research Scientist": "RSC",
    "Laboratory Technician": "LAB",
    "Manufacturing Director": "MFG",
    "Healthcare Representative": "HCR",
    "Research Director": "RDIR",
    "Sales Executive": "SEX",
    "Sales Representative": "SREP",
    "Human Resources": "HRS",
    "Manager": "MGT",
}
# Leadership roles: they form each department's management team and lead the others
LEADERSHIP_ROLES = {"Manager", "Research Director"}
TEAM_SIZE = 15            # target team size inside a (department, role) group

# Job level (1-5) -> title prefix
LEVEL_PREFIX = {1: "Junior ", 2: "", 3: "Senior ", 4: "Lead ", 5: "Principal "}

# ---------------------------------------------------------------------------
# Roles of the application. Must match the RoleName enum of the Spring
# backend (backend/.../security/domain/RoleName.java).
# ---------------------------------------------------------------------------
ROLES = [
    {"id": 1, "name": "ROLE_ADMIN", "description": "System administrator (executives)"},
    {"id": 2, "name": "ROLE_HR_MANAGER", "description": "HR manager"},
    {"id": 3, "name": "ROLE_MANAGER", "description": "Department / team manager"},
    {"id": 4, "name": "ROLE_EMPLOYEE", "description": "Standard employee"},
]
ROLE_IDS = {r["name"]: r["id"] for r in ROLES}

# Placeholder bcrypt hash that matches NO known password: seeded accounts
# cannot log in until someone sets a real password through an activation
# link (safer than 1,470 accounts sharing one public password).
DEFAULT_PASSWORD_HASH = "$2a$10$8.UnVuG9HHgffUDAlk8qfOuVGkqRzgVymGe07xd0P1R6sKz19lZ2O"

# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------
# IBM satisfaction scores are 1-4; the app shows /5
SURVEY_SOURCE_RANGE = (1, 4)
SURVEY_TARGET_RANGE = (1, 5)
PERFORMANCE_LABELS = {1: "Low", 2: "Needs Improvement", 3: "Fully Meets", 4: "Exceeds"}

# ---------------------------------------------------------------------------
# Training catalogue (the IBM file gives how MANY trainings each employee did
# last year; the course, cost and duration are chosen from this catalogue).
# Costs / durations: ranges of the Kaggle training dataset used before.
# ---------------------------------------------------------------------------
TRAINING_CATALOG = {
    "Technical Skills":       {"type": "Internal", "cost": (300, 1000), "days": (2, 5)},
    "Project Management":     {"type": "External", "cost": (400, 1000), "days": (2, 4)},
    "Leadership Development": {"type": "External", "cost": (500, 1000), "days": (2, 5)},
    "Communication Skills":   {"type": "Internal", "cost": (100, 600),  "days": (1, 3)},
    "Customer Service":       {"type": "Internal", "cost": (100, 600),  "days": (1, 3)},
    "Regulatory Compliance":  {"type": "Internal", "cost": (150, 500),  "days": (1, 2)},
}
# Which courses fit which job role (first ones are more likely)
TRAINING_BY_ROLE = {
    "Research Scientist": ["Technical Skills", "Regulatory Compliance", "Project Management"],
    "Laboratory Technician": ["Technical Skills", "Regulatory Compliance", "Communication Skills"],
    "Manufacturing Director": ["Regulatory Compliance", "Leadership Development", "Project Management"],
    "Healthcare Representative": ["Customer Service", "Regulatory Compliance", "Communication Skills"],
    "Research Director": ["Leadership Development", "Project Management", "Technical Skills"],
    "Sales Executive": ["Customer Service", "Communication Skills", "Project Management"],
    "Sales Representative": ["Customer Service", "Communication Skills"],
    "Human Resources": ["Communication Skills", "Regulatory Compliance", "Leadership Development"],
    "Manager": ["Leadership Development", "Project Management", "Communication Skills"],
}
TRAINERS = ["Amanda Daniels", "Brittany Chambers", "Carlos Mendez", "Diana Ross", "Ethan Park",
            "Fatima Zahra", "George Miller", "Hannah Lee", "Ivan Petrov", "Julia Santos"]
TRAINING_LOCATIONS = ["Training Center", "Online", "Head Office"]

# ---------------------------------------------------------------------------
# Recruitment
# ---------------------------------------------------------------------------
# Resume categories that fit each job role (the others are "unrelated" applicants)
RESUME_CATEGORIES_BY_ROLE = {
    "Sales Executive": ["SALES", "BUSINESS-DEVELOPMENT", "CONSULTANT"],
    "Sales Representative": ["SALES", "BPO", "PUBLIC-RELATIONS", "BUSINESS-DEVELOPMENT"],
    "Healthcare Representative": ["HEALTHCARE", "SALES"],
    "Laboratory Technician": ["HEALTHCARE", "AGRICULTURE", "ENGINEERING"],
    "Research Scientist": ["ENGINEERING", "AGRICULTURE", "HEALTHCARE", "INFORMATION-TECHNOLOGY"],
    "Manufacturing Director": ["ENGINEERING", "CONSTRUCTION", "AUTOMOBILE", "AVIATION"],
    "Research Director": ["ENGINEERING", "INFORMATION-TECHNOLOGY", "CONSULTANT"],
    "Human Resources": ["HR"],
    "Manager": ["CONSULTANT", "BUSINESS-DEVELOPMENT", "FINANCE"],
}
LEAVERS_PER_POSTING = 6          # one opening per ~6 leavers of the same role (min 1)
APPLICANTS_PER_POSTING = (14, 26)
RELATED_APPLICANT_SHARE = 0.65   # the rest are unrelated resumes (the AI should rank them low)
POSTING_WINDOW_DAYS = 270        # postings opened during the last ~9 months
FILLED_POSTING_SHARE = 0.3       # older postings already filled (one OFFERED application)
# Status of the other applications
APPLICATION_STATUS_WEIGHTS = {"APPLIED": 0.40, "IN REVIEW": 0.25, "INTERVIEWING": 0.15, "REJECTED": 0.20}
EDUCATION_LABELS = {1: "Below College", 2: "College", 3: "Bachelor's", 4: "Master's", 5: "PhD"}

# ---------------------------------------------------------------------------
# CV storage (MinIO) and database. Read from environment / .env.
# ---------------------------------------------------------------------------
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "applicant-cvs")

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "name": os.environ.get("DB_NAME", "smart_erp"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
}

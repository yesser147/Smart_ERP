"""
Central configuration for the Smart ERP Core ETL pipeline.
Change values here instead of hunting through the pipeline code.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_DIR = os.environ.get("ETL_INPUT_DIR", "./sample_data")
OUTPUT_DIR = os.environ.get("ETL_OUTPUT_DIR", "./output")
REPORT_DIR = os.environ.get("ETL_REPORT_DIR", "./reports")

RAW_FILES = {
    "employees": "Employee_Data.csv",
    "trainings": "Training_and_Development_Data.csv",
    "recruitment": "Recruitment_Data.csv",
    "surveys": "Employee_Engagement_Survey_Data.csv",
}

# ---------------------------------------------------------------------------
# Column ALIASES: raw Kaggle headers -> snake_case columns used everywhere
# downstream (matches the Postgres schema in schema.sql).
#
# Kaggle mirrors of this dataset use different header conventions (some use
# "Employee ID", others use "EmpID"). Each canonical field lists every known
# variant; extract.py matches them case/space/punctuation-insensitively, so
# "EmployeeStatus" and "Employee Status" both resolve to employee_status.
# If your file uses something not listed here, extract.py will warn and
# fill the column with empty values instead of crashing -- add the real
# header text to the right list below and rerun.
# ---------------------------------------------------------------------------
EMPLOYEE_ALIASES = {
    "employee_id": ["Employee ID", "EmpID", "Emp ID"],
    "first_name": ["First Name", "FirstName"],
    "last_name": ["Last Name", "LastName"],
    "start_date": ["Start Date", "StartDate", "Date of Hire", "DateofHire"],
    "exit_date": ["Exit Date", "ExitDate", "Date of Termination", "DateofTermination"],
    "title": ["Title", "Position"],
    "supervisor": ["Supervisor", "Manager Name", "ManagerName"],
    "email": ["Email", "ADEmail", "AD Email", "E-mail"],
    "business_unit": ["Business Unit", "BusinessUnit"],
    "employee_status": ["Employee Status", "EmployeeStatus", "Employment Status", "EmploymentStatus"],
    "employee_type": ["Employee Type", "EmployeeType"],
    "pay_zone": ["Pay Zone", "PayZone"],
    "employee_classification_type": ["Employee Classification Type", "EmployeeClassificationType"],
    "termination_type": ["Termination Type", "TerminationType", "Term Reason", "TermReason"],
    "termination_description": ["Termination Description", "TerminationDescription"],
    "department_type": ["Department Type", "DepartmentType", "Department"],
    "division_description": ["Division Description", "Division"],
    "dob": ["DOB", "Date of Birth", "DateOfBirth"],
    "state": ["State"],
    "job_function": ["Job Function", "JobFunctionDescription", "Job Function Description"],
    "gender": ["Gender", "GenderCode", "Sex"],
    "location": ["Location", "LocationCode"],
    "race_ethnicity": ["Race (or) Ethnicity", "RaceDesc", "Race"],
    "marital_status": ["Marital Status", "MaritalDesc"],
    "performance_score": ["Performance Score", "PerformanceScore"],
    "current_employee_rating": ["Current Employee Rating", "CurrentEmployeeRating"],
}

TRAINING_ALIASES = {
    "employee_id": ["Employee ID", "EmpID", "Emp ID"],
    "training_date": ["Training Date", "TrainingDate"],
    "training_program_name": ["Training Program Name", "TrainingProgramName", "Program Name"],
    "training_type": ["Training Type", "TrainingType"],
    "training_outcome": ["Training Outcome", "TrainingOutcome"],
    "location": ["Location"],
    "trainer": ["Trainer"],
    "training_duration_days": [
        "Training Duration (Days)", "Training Duration(Days)", "Training Duration Days",
        "TrainingDuration", "Duration (Days)", "Duration Days", "Training Duration",
    ],
    "training_cost": ["Training Cost", "TrainingCost"],
}

RECRUITMENT_ALIASES = {
    "applicant_id": ["Applicant ID", "ApplicantID"],
    "application_date": ["Application Date", "ApplicationDate"],
    "first_name": ["First Name", "FirstName"],
    "last_name": ["Last Name", "LastName"],
    "gender": ["Gender", "GenderCode", "Sex"],
    "dob": ["Date of Birth", "DOB", "DateOfBirth"],
    "phone_number": ["Phone Number", "Phone", "PhoneNumber"],
    "email": ["Email", "E-mail"],
    "address": ["Address"],
    "city": ["City"],
    "state": ["State"],
    "zip_code": ["Zip Code", "Zip", "ZipCode"],
    "country": ["Country"],
    "education_level": ["Education Level", "EducationLevel"],
    "years_of_experience": ["Years of Experience", "YearsOfExperience"],
    "desired_salary": ["Desired Salary", "DesiredSalary"],
    "job_title": ["Job Title", "JobTitle"],
    "status": ["Status"],
}

SURVEY_ALIASES = {
    "employee_id": ["Employee ID", "EmpID", "Emp ID"],
    "survey_date": ["Survey Date", "SurveyDate"],
    "engagement_score": ["Engagement Score", "EngagementScore"],
    "satisfaction_score": ["Satisfaction Score", "SatisfactionScore"],
    "work_life_balance_score": ["Work-Life Balance Score", "WorkLifeBalanceScore", "Work Life Balance Score"],
}

# Columns dropped from the employee table: sensitive / not used anywhere in
# the app. Edit this list freely -- nothing else depends on it.
EMPLOYEE_DROP_COLUMNS = ["race_ethnicity", "marital_status", "pay_zone"]

# ---------------------------------------------------------------------------
# Business rule bounds -- these are ASSUMPTIONS since we don't have your
# actual CSV in front of us. Check your real data's min/max before trusting
# them (a one-liner is in README.md) and adjust here if needed.
# ---------------------------------------------------------------------------
MIN_WORKING_AGE = 16
MAX_PLAUSIBLE_AGE = 75
RATING_RANGE = (1, 5)          # current_employee_rating
SURVEY_SCORE_RANGE = (1, 5)    # engagement / satisfaction / work-life scores
MAX_YEARS_EXPERIENCE = 50
FUTURE_EXIT_TOLERANCE_DAYS = 365  # exit dates further than this in the future are flagged

CANONICAL_STATUSES = {
    "ACTIVE": "Active",
    "TERMINATED": "Terminated",
    "ON LEAVE": "On Leave",
    "LEAVE OF ABSENCE": "On Leave",
}

# ---------------------------------------------------------------------------
# Max text length per column, mirroring the VARCHAR widths in schema.sql
# (with a little safety margin). This dataset is Faker-generated, and
# Faker occasionally emits garbage where a formatted field (usually a
# phone number) should be -- a run of hundreds of '#' placeholder
# characters left over from a template substitution that failed. Anything
# over these lengths is treated as corrupted, not real data: nulled and
# flagged rather than crashing the DB insert on a VARCHAR overflow.
# ---------------------------------------------------------------------------
MAX_FIELD_LENGTHS = {
    "employees": {
        "first_name": 100, "last_name": 100, "title": 150, "email": 255,
        "employee_status": 50, "employee_type": 50, "employee_classification_type": 50,
        "termination_type": 100, "state": 50, "job_function": 255, "gender": 20,
        "location": 50, "performance_score": 50,
    },
    "trainings": {
        "training_program_name": 255, "training_type": 100, "training_outcome": 100,
        "location": 150, "trainer": 150,
    },
    "recruitment": {
        "first_name": 100, "last_name": 100, "gender": 20, "phone_number": 30,
        "email": 255, "city": 100, "state": 100, "zip_code": 20, "country": 100,
        "education_level": 100, "job_title": 150, "status": 50,
    },
    "surveys": {},
}

# ---------------------------------------------------------------------------
# Synthesized identity / recruitment tables
# ---------------------------------------------------------------------------
ROLES = [
    {"id": 1, "name": "ROLE_SUPER_ADMIN", "description": "Full system access"},
    {"id": 2, "name": "ROLE_ADMIN", "description": "HR administrator"},
    {"id": 3, "name": "ROLE_MANAGER", "description": "Department / team manager"},
    {"id": 4, "name": "ROLE_USER", "description": "Standard employee"},
]
# bcrypt hash of "Password123!" -- every seeded user shares it, they should
# reset on first login. Swap this for real onboarding logic later.
DEFAULT_PASSWORD_HASH = "$2a$10$8.UnVuG9HHgffUDAlk8qfOuVGkqRzgVymGe07xd0P1R6sKz19lZ2O"

# ---------------------------------------------------------------------------
# Database connection (used by load.py). Reads from environment / .env.
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "name": os.environ.get("DB_NAME", "smart_erp"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
}
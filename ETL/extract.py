"""
Extract stage: reads the raw sources into memory. No cleaning here
(that's clean.py's job).

  - employees: IBM HR Analytics attrition file (one row per employee)
  - resumes:   Kaggle Resume dataset (one row per real resume)
"""

import os
import pandas as pd
import config

# Columns the rest of the pipeline relies on
EMPLOYEE_COLUMNS = [
    "EmployeeNumber", "Age", "Attrition", "BusinessTravel", "Department", "DistanceFromHome",
    "Education", "EducationField", "EnvironmentSatisfaction", "Gender", "JobInvolvement",
    "JobLevel", "JobRole", "JobSatisfaction", "MaritalStatus", "MonthlyIncome",
    "NumCompaniesWorked", "OverTime", "PercentSalaryHike", "PerformanceRating",
    "RelationshipSatisfaction", "StockOptionLevel", "TotalWorkingYears",
    "TrainingTimesLastYear", "WorkLifeBalance", "YearsAtCompany", "YearsInCurrentRole",
    "YearsSinceLastPromotion", "YearsWithCurrManager",
]
RESUME_COLUMNS = ["ID", "Resume_str", "Category"]


def _read_csv_safely(path):
    """utf-8 (with or without BOM) first, latin-1 as a fallback."""
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        print(f"  utf-8 failed for {os.path.basename(path)}, retrying with latin-1")
        df = pd.read_csv(path, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    return df


def _require_columns(df, columns, name):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: missing columns {missing}. Is this the right file?")


def extract_employees():
    for filename in config.EMPLOYEE_FILES:
        path = os.path.join(config.INPUT_DIR, filename)
        if os.path.exists(path):
            df = _read_csv_safely(path)
            _require_columns(df, EMPLOYEE_COLUMNS, filename)
            print(f"  loaded employees: {len(df)} rows from {filename}")
            return df
    raise FileNotFoundError(
        f"None of {config.EMPLOYEE_FILES} found in {config.INPUT_DIR}. Download the IBM HR "
        f"Analytics attrition dataset (Kaggle: pavansubhasht/ibm-hr-analytics-attrition-dataset)."
    )


def extract_resumes():
    if not os.path.exists(config.RESUME_CSV):
        raise FileNotFoundError(
            f"{config.RESUME_CSV} not found. Download the Kaggle Resume dataset "
            f"(snehaanbhawal/resume-dataset) into sample_data/Resume and sample_data/data."
        )
    df = _read_csv_safely(config.RESUME_CSV)
    _require_columns(df, RESUME_COLUMNS, "Resume.csv")
    print(f"  loaded resumes: {len(df)} rows")
    return df[RESUME_COLUMNS].copy()


def extract_all():
    print("EXTRACT")
    return {"employees": extract_employees(), "resumes": extract_resumes()}

"""
Clean stage: types, ranges, duplicates and consistency checks on the two
sources. Every rule logs how many rows it touched in the DataQualityReport,
so nothing changes silently.
"""

import os
import re
import pandas as pd
import config

# Valid ranges of the IBM numeric columns (documented in the dataset)
EMPLOYEE_RANGES = {
    "Age": (18, 70), "DistanceFromHome": (0, 100), "Education": (1, 5),
    "EnvironmentSatisfaction": (1, 4), "JobInvolvement": (1, 4), "JobLevel": (1, 5),
    "JobSatisfaction": (1, 4), "MonthlyIncome": (500, 50000), "NumCompaniesWorked": (0, 20),
    "PercentSalaryHike": (0, 50), "PerformanceRating": (1, 4), "RelationshipSatisfaction": (1, 4),
    "StockOptionLevel": (0, 3), "TotalWorkingYears": (0, 50), "TrainingTimesLastYear": (0, 10),
    "WorkLifeBalance": (1, 4), "YearsAtCompany": (0, 50), "YearsInCurrentRole": (0, 50),
    "YearsSinceLastPromotion": (0, 50), "YearsWithCurrManager": (0, 50),
}
TEXT_COLUMNS = ["Attrition", "BusinessTravel", "Department", "EducationField", "Gender",
                "JobRole", "MaritalStatus", "OverTime"]
MIN_RESUME_CHARS = 200


def clean_employees(df, report):
    table = "employees"
    df = df.copy()

    for col in TEXT_COLUMNS:
        df[col] = df[col].astype("string").str.strip()

    # 1. Primary key
    df["EmployeeNumber"] = pd.to_numeric(df["EmployeeNumber"], errors="coerce")
    missing = df["EmployeeNumber"].isna()
    report.log(table, "missing_id_dropped", int(missing.sum()), "Rows without EmployeeNumber dropped")
    df = df[~missing]
    dupes = df.duplicated(subset=["EmployeeNumber"], keep="first")
    report.log(table, "duplicate_id_dropped", int(dupes.sum()), "Duplicate EmployeeNumber: first kept")
    df = df[~dupes].copy()
    df["EmployeeNumber"] = df["EmployeeNumber"].astype(int)

    # 2. Numeric columns: type + documented range
    for col, (lo, hi) in EMPLOYEE_RANGES.items():
        values = pd.to_numeric(df[col], errors="coerce")
        bad = values.isna() | (values < lo) | (values > hi)
        report.log(table, f"{col}_invalid_dropped", int(bad.sum()),
                   f"{col} missing or outside [{lo}, {hi}] -> row dropped")
        df = df[~bad].copy()
        df[col] = values[~bad].astype(int)

    # 3. Categorical columns must have a known value
    known = {
        "Attrition": {"Yes", "No"}, "OverTime": {"Yes", "No"}, "Gender": {"Male", "Female"},
        "Department": set(config.DEPARTMENT_CODES), "JobRole": set(config.ROLE_CODES),
    }
    for col, values in known.items():
        bad = ~df[col].isin(values)
        report.log(table, f"{col}_unknown_dropped", int(bad.sum()), f"{col} not in {sorted(values)} -> row dropped")
        df = df[~bad].copy()

    # 4. Logical consistency (impossible combinations are dropped, not guessed)
    rules = [
        ("years_at_company_gt_total", df["YearsAtCompany"] > df["TotalWorkingYears"],
         "YearsAtCompany greater than TotalWorkingYears"),
        ("years_in_role_gt_company", df["YearsInCurrentRole"] > df["YearsAtCompany"],
         "YearsInCurrentRole greater than YearsAtCompany"),
        ("years_with_manager_gt_company", df["YearsWithCurrManager"] > df["YearsAtCompany"],
         "YearsWithCurrManager greater than YearsAtCompany"),
        ("started_working_before_14", (df["Age"] - df["TotalWorkingYears"]) < 14,
         "Age - TotalWorkingYears < 14"),
    ]
    for rule, mask, description in rules:
        report.log(table, rule, int(mask.sum()), f"{description} -> row dropped")
        df = df[~mask].copy()

    print(f"  employees cleaned: {len(df)} rows kept")
    return df.reset_index(drop=True)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def clean_resumes(df, report):
    table = "resumes"
    df = df.copy()
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df["Category"] = df["Category"].astype("string").str.strip().str.upper()
    df["Resume_str"] = df["Resume_str"].fillna("").map(_normalize_text)

    missing = df["ID"].isna()
    report.log(table, "missing_id_dropped", int(missing.sum()), "Resume without ID dropped")
    df = df[~missing].copy()
    df["ID"] = df["ID"].astype(int)

    dupes = df.duplicated(subset=["ID"], keep="first")
    report.log(table, "duplicate_id_dropped", int(dupes.sum()), "Duplicate resume ID: first kept")
    df = df[~dupes]

    short = df["Resume_str"].str.len() < MIN_RESUME_CHARS
    report.log(table, "too_short_dropped", int(short.sum()),
               f"Resume text shorter than {MIN_RESUME_CHARS} characters (nothing to analyse) -> dropped")
    df = df[~short].copy()

    # PDF file of the resume (uploaded to MinIO by the load step when present)
    df["pdf_path"] = [os.path.join(config.RESUME_PDF_DIR, str(c), f"{i}.pdf") for c, i in zip(df["Category"], df["ID"])]
    no_pdf = ~df["pdf_path"].map(os.path.exists)
    report.log(table, "pdf_missing", int(no_pdf.sum()), "No PDF on disk: the text is still used")
    df.loc[no_pdf, "pdf_path"] = None

    print(f"  resumes cleaned: {len(df)} rows kept")
    return df.reset_index(drop=True)

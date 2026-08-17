"""
Transform stage: Synthesizes fully normalized tables for security tokens, 
training catalogs, ATS workflows, salary history, and pgvector embeddings.
"""

import uuid
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
import config


def extract_departments(employees, report):
    dept_cols = ["business_unit", "department_type", "division_description"]
    dept_cols = [c for c in dept_cols if c in employees.columns]
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    departments = employees[dept_cols].drop_duplicates().reset_index(drop=True)
    departments.index += 1
    departments.index.name = "department_id"
    departments = departments.reset_index()

    departments["is_deleted"] = False
    departments["created_at"] = now_str

    employees = employees.merge(departments, on=dept_cols, how="left")
    employees = employees.drop(columns=dept_cols)

    report.log("departments", "extracted", len(departments),
               f"{len(departments)} unique departments extracted")
    return employees, departments


def link_managers(employees, report):
    employees = employees.copy()
    employees["full_name"] = employees["first_name"] + " " + employees["last_name"]

    name_counts = employees["full_name"].value_counts()
    name_to_id = employees.drop_duplicates(subset="full_name", keep="first").set_index("full_name")["employee_id"]

    employees["manager_id"] = employees["supervisor"].map(name_to_id)
    self_ref_mask = employees["manager_id"] == employees["employee_id"]
    if self_ref_mask.any():
        employees.loc[self_ref_mask, "manager_id"] = np.nan

    employees["manager_id"] = pd.to_numeric(employees["manager_id"], errors="coerce").astype("Int64")
    valid_emp_ids = set(employees["employee_id"])
    invalid_manager_mask = employees["manager_id"].notna() & ~employees["manager_id"].isin(valid_emp_ids)
    
    if invalid_manager_mask.any():
        employees.loc[invalid_manager_mask, "manager_id"] = pd.NA

    employees = employees.drop(columns=["full_name", "supervisor"])
    return employees


def build_roles():
    return pd.DataFrame(config.ROLES)


def build_users(employees, report):
    manager_ids = set(employees["manager_id"].dropna())

    def role_for(row):
        title = str(row["title"]).upper()
        if "CEO" in title or "PRESIDENT" in title or "CHIEF" in title:
            return 1  # SUPER_ADMIN
        if "DIRECTOR" in title or "VP" in title or "HEAD OF" in title:
            return 2  # ADMIN
        if "MANAGER" in title or "SUPERVISOR" in title or "LEAD" in title or row["employee_id"] in manager_ids:
            return 3  # MANAGER
        return 4  # USER

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    users = pd.DataFrame({
        "id": [str(uuid.uuid4()) for _ in range(len(employees))],
        "employee_id": employees["employee_id"].values,
        "email": employees["email"].values,
        "password_hash": config.DEFAULT_PASSWORD_HASH,
        "is_active": employees["employee_status"].eq("Active").values,
        "role_id": employees.apply(role_for, axis=1).values,
        "created_at": now_str,
        "updated_at": now_str,
        "created_by": "SYSTEM_ETL",
        "updated_by": "SYSTEM_ETL"
    })

    report.log("users", "generated", len(users), "Clean user domain accounts generated")
    return users


def build_user_tokens(users, report):
    """Generates activation tokens in dedicated user_tokens table for inactive users."""
    inactive_users = users[users["is_active"] == False].copy()
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=7)

    tokens = pd.DataFrame({
        "id": [str(uuid.uuid4()) for _ in range(len(inactive_users))],
        "user_id": inactive_users["id"].values,
        "token": [str(uuid.uuid4()) for _ in range(len(inactive_users))],
        "token_type": "ACTIVATION",
        "expires_at": expiry.strftime("%Y-%m-%d %H:%M:%S"),
        "is_used": False,
        "is_revoked": False,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
    })

    report.log("user_tokens", "generated", len(tokens), "Activation tokens written to user_tokens table")
    return tokens


def inject_compensation_and_history(employees, users, report):
    """Injects current salary and creates initial entries in salary_history table."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    emp = employees.merge(users[["employee_id", "role_id"]], on="employee_id", how="left")
    rng = np.random.default_rng(42)

    def generate_salary(role_id):
        if role_id == 1: return round(rng.uniform(150000, 250000), 2)
        if role_id == 2: return round(rng.uniform(95000, 145000), 2)
        if role_id == 3: return round(rng.uniform(70000, 105000), 2)
        return round(rng.uniform(45000, 80000), 2)

    employees["salary"] = emp["role_id"].apply(generate_salary)
    employees["currency"] = "USD"
    employees["is_deleted"] = False
    employees["created_at"] = now_str
    employees["updated_at"] = now_str

    salary_history = pd.DataFrame({
        "employee_id": employees["employee_id"].values,
        "effective_date": employees["start_date"].values,
        "salary": employees["salary"].values,
        "currency": "USD",
        "change_reason": "INITIAL_HIRE",
        "created_at": now_str
    })

    report.log("salary_history", "generated", len(salary_history), "Initial compensation histories generated")
    return employees, salary_history


def normalize_trainings(raw_trainings, report):
    """Splits flat trainings into training_courses catalog and employee_trainings logs."""
    course_cols = ["training_program_name", "training_type", "trainer", "training_duration_days", "training_cost"]
    
    # 1. Deduplicate strictly by program_name to respect the UNIQUE constraint
    courses = raw_trainings[course_cols].drop_duplicates(subset=["training_program_name"]).reset_index(drop=True)
    
    courses.rename(columns={
        "training_program_name": "program_name",
        "training_duration_days": "duration_days",
        "training_cost": "cost"
    }, inplace=True)
    courses["is_active"] = True

    # 2. Assign explicit IDs for foreign key linking
    courses.index += 1
    courses.index.name = "course_id"
    courses = courses.reset_index()

    # 3. Join on program_name only
    merged = raw_trainings.merge(courses, left_on="training_program_name", right_on="program_name", how="left")

    employee_trainings = pd.DataFrame({
        "employee_id": merged["employee_id"].values,
        "course_id": merged["course_id"].values,
        "training_date": merged["training_date"].values,
        "completion_status": merged["training_outcome"].values,
        "location": merged["location"].values
    })

    report.log("training_courses", "extracted", len(courses), "Extracted training catalog")
    report.log("employee_trainings", "linked", len(employee_trainings), "Normalized employee training logs")
    return courses, employee_trainings


def normalize_recruitment(raw_recruitment, departments, report):
    """Splits raw recruitment data into applicants, job_postings, and job_applications."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    applicant_cols = [
        "applicant_id", "first_name", "last_name", "email", "phone_number", 
        "education_level", "years_of_experience", "gender", "dob", "address", 
        "city", "state", "zip_code", "country"
    ]
    applicant_cols = [c for c in applicant_cols if c in raw_recruitment.columns]
    
    # 1. Deduplicate by email and applicant_id to satisfy DB UNIQUE constraints
    applicants = (
        raw_recruitment[applicant_cols]
        .drop_duplicates(subset=["email"])
        .drop_duplicates(subset=["applicant_id"])
        .copy()
    )
    applicants["created_at"] = now_str

    # Filter raw recruitment records to retain valid FK relationships
    valid_applicant_ids = set(applicants["applicant_id"])
    valid_recruitment = raw_recruitment[raw_recruitment["applicant_id"].isin(valid_applicant_ids)].copy()

    # 2. Job Postings
    unique_titles = valid_recruitment["job_title"].dropna().unique()
    rng = np.random.default_rng(42)
    
    dept_ids = departments["department_id"].tolist() if len(departments) > 0 else [1]
    
    job_postings = pd.DataFrame({
        "job_id": range(1, len(unique_titles) + 1),
        "title": unique_titles,
        "department_id": [rng.choice(dept_ids) for _ in range(len(unique_titles))],
        "location": "Remote / HQ",
        "required_experience_years": rng.integers(1, 8, size=len(unique_titles)),
        "offered_salary_min": rng.integers(50000, 75000, size=len(unique_titles)),
        "offered_salary_max": rng.integers(80000, 130000, size=len(unique_titles)),
        "status": "OPEN",
        "created_at": now_str
    })

    title_to_job_id = dict(zip(job_postings["title"], job_postings["job_id"]))

    # 3. Job Applications (linked only to surviving applicants)
    applications = pd.DataFrame({
        "application_id": [str(uuid.uuid4()) for _ in range(len(valid_recruitment))],
        "applicant_id": valid_recruitment["applicant_id"].values,
        "job_id": valid_recruitment["job_title"].map(title_to_job_id).fillna(1).astype(int).values,
        "application_date": valid_recruitment["application_date"].values,
        "desired_salary": valid_recruitment["desired_salary"].values,
        "status": valid_recruitment["status"].values,
        "ai_match_score": rng.integers(45, 98, size=len(valid_recruitment)),
        "created_at": now_str
    })

    report.log("applicants", "extracted", len(applicants), "Normalized applicant profiles")
    report.log("job_postings", "generated", len(job_postings), "Extracted job requisitions")
    report.log("job_applications", "linked", len(applications), "Created job application links")
    return applicants, job_postings, applications


def build_applicant_cvs(applicants, report):
    """Generates applicant CV records with 384-dimension embeddings."""
    rng = np.random.default_rng(42)
    
    def generate_vector():
        vec = rng.normal(0, 1, 384)
        vec_norm = vec / np.linalg.norm(vec)
        return "[" + ",".join(map(str, np.round(vec_norm, 6))) + "]"

    cvs = pd.DataFrame({
        "id": [str(uuid.uuid4()) for _ in range(len(applicants))],
        "applicant_id": applicants["applicant_id"].values,
        "file_url": [f"/storage/cvs/{aid}_cv.pdf" for aid in applicants["applicant_id"]],
        "parsed_text": [
            f"{row.first_name} {row.last_name} with "
            f"{row.years_of_experience if pd.notna(row.years_of_experience) else 'unspecified'} "
            f"years experience."
            for row in applicants.itertuples()
        ],
        "extracted_skills_json": [
            json.dumps(["Java", "Spring Boot", "SQL", "Problem Solving"])
            for _ in range(len(applicants))
        ],
        "cv_embedding": [generate_vector() for _ in range(len(applicants))],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    })

    report.log("applicant_cvs", "synthesized", len(cvs), "Generated vector embeddings for pgvector search")
    return cvs


def enforce_manager_hierarchy(employees, users, report):
    employees = employees.copy()
    emp = employees.merge(users[["employee_id", "role_id"]], on="employee_id", how="left")

    executives = emp[emp["role_id"] == 1]["employee_id"].tolist()
    dept_admins = emp[emp["role_id"] <= 2].groupby("department_id")["employee_id"].apply(list).to_dict()
    dept_managers = emp[emp["role_id"] <= 3].groupby("department_id")["employee_id"].apply(list).to_dict()

    def assign_manager(row):
        if pd.notna(row["manager_id"]): return row["manager_id"]
        dept, role, emp_id = row["department_id"], row["role_id"], row["employee_id"]

        if role == 1: return pd.NA
        if role == 2:
            candidates = [c for c in executives if c != emp_id]
            return candidates[0] if candidates else pd.NA
        if role == 3:
            candidates = [c for c in dept_admins.get(dept, []) if c != emp_id]
            if candidates: return candidates[0]
            candidates = [c for c in executives if c != emp_id]
            return candidates[0] if candidates else pd.NA
        if role == 4:
            candidates = [c for c in dept_managers.get(dept, []) if c != emp_id]
            if candidates: return candidates[0]
            candidates = [c for c in dept_admins.get(dept, []) if c != emp_id]
            if candidates: return candidates[0]
            candidates = [c for c in executives if c != emp_id]
            return candidates[0] if candidates else pd.NA

        return pd.NA

    employees["manager_id"] = emp.apply(assign_manager, axis=1).astype("Int64")
    return employees

def run_transform(cleaned, report):
    print("TRANSFORM")
    
    # -------------------------------------------------------------------
    # NEW: Safely enforce employee_id as an integer across all dataframes
    # -------------------------------------------------------------------
    cleaned["employees"]["employee_id"] = pd.to_numeric(
        cleaned["employees"]["employee_id"], errors="coerce"
    ).astype("Int64")
    
    if "employee_id" in cleaned["trainings"].columns:
        cleaned["trainings"]["employee_id"] = pd.to_numeric(
            cleaned["trainings"]["employee_id"], errors="coerce"
        ).astype("Int64")
        
    if "employee_id" in cleaned["surveys"].columns:
        cleaned["surveys"]["employee_id"] = pd.to_numeric(
            cleaned["surveys"]["employee_id"], errors="coerce"
        ).astype("Int64")
    # -------------------------------------------------------------------

    employees, departments = extract_departments(cleaned["employees"], report)
    employees = link_managers(employees, report)
    roles = build_roles()
    
    users = build_users(employees, report)
    user_tokens = build_user_tokens(users, report)
    
    employees = enforce_manager_hierarchy(employees, users, report)
    employees, salary_history = inject_compensation_and_history(employees, users, report)
    
    if "email" in employees.columns:
        employees = employees.drop(columns=["email"])

    courses, employee_trainings = normalize_trainings(cleaned["trainings"], report)
    applicants, job_postings, job_applications = normalize_recruitment(cleaned["recruitment"], departments, report)
    cvs = build_applicant_cvs(applicants, report)

    return {
        "roles": roles,
        "departments": departments,
        "employees": employees,
        "salary_history": salary_history,
        "users": users,
        "user_tokens": user_tokens,
        "training_courses": courses,
        "employee_trainings": employee_trainings,
        "surveys": cleaned["surveys"],
        "applicants": applicants,
        "job_postings": job_postings,
        "job_applications": job_applications,
        "applicant_cvs": cvs,
    }
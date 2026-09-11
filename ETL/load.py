"""
Load stage: Exports clean CSVs and loads all 13 normalized tables into PostgreSQL.
"""

import os
import pandas as pd
import config

LOAD_ORDER = [
    "roles",
    "departments",
    "employees",
    "salary_history",
    "users",
    "user_tokens",
    "training_courses",
    "employee_trainings",
    "surveys",
    "applicants",
    "job_postings",
    "job_applications",
    "applicant_cvs",
]

CSV_FILENAMES = {
    "roles": "pg_roles.csv",
    "departments": "pg_departments.csv",
    "employees": "pg_employees.csv",
    "salary_history": "pg_salary_history.csv",
    "users": "pg_users.csv",
    "user_tokens": "pg_user_tokens.csv",
    "training_courses": "pg_training_courses.csv",
    "employee_trainings": "pg_employee_trainings.csv",
    "surveys": "pg_surveys.csv",
    "applicants": "pg_applicants.csv",
    "job_postings": "pg_job_postings.csv",
    "job_applications": "pg_job_applications.csv",
    "applicant_cvs": "pg_cvs.csv",
}

SQL_TABLE_NAMES = {
    "roles": "roles",
    "departments": "departments",
    "employees": "employees",
    "salary_history": "salary_history",
    "users": "users",
    "user_tokens": "user_tokens",
    "training_courses": "training_courses",
    "employee_trainings": "employee_trainings",
    "surveys": "engagement_surveys",
    "applicants": "applicants",
    "job_postings": "job_postings",
    "job_applications": "job_applications",
    "applicant_cvs": "applicant_cvs",
}

# NOTE: department_budget_allocations is deliberately NOT in LOAD_ORDER /
# CSV_FILENAMES / SQL_TABLE_NAMES above. It isn't sourced from the Kaggle
# CSVs -- it's live data the Spring Boot app writes when an HR manager
# confirms a budget. See backup_budget_allocations() / 
# restore_budget_allocations() below for how it survives a full ETL rerun.


def export_csvs(tables):
    print("LOAD -- exporting cleaned CSVs")
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    for key in LOAD_ORDER:
        path = os.path.join(config.OUTPUT_DIR, CSV_FILENAMES[key])
        tables[key].to_csv(path, index=False)
        print(f"  wrote {path} ({len(tables[key])} rows)")


def build_engine():
    from sqlalchemy import create_engine
    url = (
        f"postgresql+psycopg2://{config.DB_CONFIG['user']}:{config.DB_CONFIG['password']}"
        f"@{config.DB_CONFIG['host']}:{config.DB_CONFIG['port']}/{config.DB_CONFIG['name']}"
    )
    return create_engine(url)


def backup_budget_allocations(engine):
    """Runs BEFORE apply_schema(). apply_schema drops departments/users with
    CASCADE, which silently takes department_budget_allocations down with it
    if the table already exists. Read it out into memory first so it can be
    restored after the schema (and departments/users) are rebuilt.

    Returns an empty DataFrame on first-ever run, when the table doesn't
    exist yet -- that's expected, not an error."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM department_budget_allocations;"), conn)
        print(f"  backed up {len(df)} existing budget allocation(s) before schema rebuild")
        return df
    except Exception:
        print("  no existing department_budget_allocations table found -- first run, nothing to back up")
        return pd.DataFrame()


def restore_budget_allocations(engine, backup_df):
    """Runs AFTER apply_schema() and the department/user reload. Only
    restores rows whose department_id still exists post-reload -- if you
    ever change the source CSVs (different rows, different order), department
    IDs can shift and this will correctly skip orphaned rows rather than
    violating the FK."""
    if backup_df.empty:
        return

    from sqlalchemy import text
    with engine.begin() as conn:
        valid_dept_ids = set(
            row[0] for row in conn.execute(text("SELECT department_id FROM departments;")).fetchall()
        )
        valid_user_ids = set(
            str(row[0]) for row in conn.execute(text("SELECT id FROM users;")).fetchall()
        )

    restorable = backup_df[backup_df["department_id"].isin(valid_dept_ids)].copy()
    orphaned = len(backup_df) - len(restorable)
    if orphaned:
        print(f"  WARNING: {orphaned} budget allocation(s) referenced a department_id that no "
              f"longer exists after reload -- likely because the source CSV changed. Skipped, not restored.")

    # approved_by is a nullable FK to users -- null it out rather than drop
    # the whole row if that specific user no longer exists post-reload.
    if "approved_by" in restorable.columns:
        restorable.loc[~restorable["approved_by"].astype(str).isin(valid_user_ids), "approved_by"] = None

    if not restorable.empty:
        with engine.begin() as conn:
            restorable.to_sql("department_budget_allocations", conn, if_exists="append", index=False)
        print(f"  restored {len(restorable)} budget allocation(s) after schema rebuild")


def apply_schema(engine, schema_path="schema.sql"):
    from sqlalchemy import text
    with open(schema_path) as f:
        ddl = f.read()
    with engine.begin() as conn:
        for statement in ddl.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    print("  schema applied successfully")


def load_to_postgres(tables, apply_schema_first=True):
    print("LOAD -- writing to Postgres")
    engine = build_engine()

    budget_backup = pd.DataFrame()
    if apply_schema_first:
        budget_backup = backup_budget_allocations(engine)
        apply_schema(engine)

    from sqlalchemy import text

    with engine.begin() as conn:
        for key in LOAD_ORDER:
            sql_name = SQL_TABLE_NAMES[key]
            tables[key].to_sql(sql_name, conn, if_exists="append", index=False, method="multi", chunksize=500)
            print(f"  loaded {sql_name}: {len(tables[key])} rows")

        # Sync SERIAL sequences so future manual inserts don't collide with bulk IDs
        serial_tables = [
            ("roles", "id"),
            ("departments", "department_id"),
            ("training_courses", "course_id"),
            ("job_postings", "job_id"),
            ("salary_history", "id"),
            ("employee_trainings", "id"),
            ("engagement_surveys", "id"),
        ]
        for tbl, col in serial_tables:
            conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{tbl}', '{col}'), coalesce(max({col}), 1)) FROM {tbl};"))

    if apply_schema_first:
        restore_budget_allocations(engine, budget_backup)

    print("  done -- all 13 ETL tables loaded, plus any restored budget allocations")
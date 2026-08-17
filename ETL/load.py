"""
Load stage: Exports clean CSVs and loads all 13 normalized tables into PostgreSQL.
"""

import os
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

    if apply_schema_first:
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

    print("  done -- all 13 tables loaded inside a single transaction")
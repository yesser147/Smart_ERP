"""
Load stage: exports the clean tables as CSV, loads the tables into
PostgreSQL, uploads the resume PDFs to MinIO and seeds the required skills
per job title.
"""

import os
import re
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
    "performance_reviews",
    "leave_requests",
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
    "performance_reviews": "pg_performance_reviews.csv",
    "leave_requests": "pg_leave_requests.csv",
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
    "performance_reviews": "performance_reviews",
    "leave_requests": "leave_requests",
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
            # remember the team code: department ids may point to other teams after a reload
            df = pd.read_sql(text("""
                SELECT a.*, d.business_unit AS _business_unit
                FROM department_budget_allocations a
                LEFT JOIN departments d ON d.department_id = a.department_id
            """), conn)
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
        dept_by_code = dict(
            (row[1], row[0]) for row in
            conn.execute(text("SELECT department_id, business_unit FROM departments;")).fetchall()
        )
        valid_user_ids = set(
            str(row[0]) for row in conn.execute(text("SELECT id FROM users;")).fetchall()
        )

    # re-attach each allocation to the team with the same code, drop the others
    restorable = backup_df.copy()
    restorable["department_id"] = restorable["_business_unit"].map(dept_by_code)
    restorable = restorable[restorable["department_id"].notna()].drop(columns=["_business_unit"])
    orphaned = len(backup_df) - len(restorable)
    if orphaned:
        print(f"  WARNING: {orphaned} budget allocation(s) referenced a department_id that no "
              f"longer exists after reload -- likely because the source data changed. Skipped, not restored.")

    # approved_by is a nullable FK to users -- null it out rather than drop
    # the whole row if that specific user no longer exists post-reload.
    if "approved_by" in restorable.columns:
        restorable.loc[~restorable["approved_by"].astype(str).isin(valid_user_ids), "approved_by"] = None

    if not restorable.empty:
        with engine.begin() as conn:
            restorable.to_sql("department_budget_allocations", conn, if_exists="append", index=False)
        print(f"  restored {len(restorable)} budget allocation(s) after schema rebuild")


def _run_sql_file(conn, path):
    """Runs a whole .sql file in one go through the raw psycopg2 cursor, so
    semicolons inside comments or strings can't split a statement."""
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    with conn.connection.cursor() as cur:
        cur.execute(sql)


def _migration_files():
    """Backend Flyway versioned migrations (V1__..., V2__...) in version order."""
    files = [f for f in os.listdir(config.MIGRATIONS_DIR) if re.match(r"^V\d+__.*\.sql$", f)]
    files.sort(key=lambda f: int(re.match(r"^V(\d+)__", f).group(1)))
    return [os.path.join(config.MIGRATIONS_DIR, f) for f in files]


def apply_schema(engine, reset_path=os.path.join(os.path.dirname(__file__), "schema.sql")):
    """Drops everything (schema.sql), then builds the schema from the backend's
    migrations -- the single source of truth for the database structure."""
    with engine.begin() as conn:
        _run_sql_file(conn, reset_path)
        for path in _migration_files():
            _run_sql_file(conn, path)
            print(f"  applied {os.path.basename(path)}")
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
            ("employees", "employee_id"),
            ("applicants", "applicant_id"),  # new applicants from the app must not reuse CSV ids
            ("performance_reviews", "id"),
            ("leave_requests", "id"),
        ]
        for tbl, col in serial_tables:
            conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{tbl}', '{col}'), coalesce(max({col}), 1)) FROM {tbl};"))

    if apply_schema_first:
        restore_budget_allocations(engine, budget_backup)

    print("  done -- all ETL tables loaded, plus any restored budget allocations")


def upload_cv_pdfs(cv_files):
    """Uploads each applicant's resume PDF to the (private) MinIO bucket, at
    the file_url already written in applicant_cvs."""
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    print("LOAD -- uploading resume PDFs to MinIO")
    s3 = boto3.client("s3", endpoint_url=config.MINIO_ENDPOINT,
                      aws_access_key_id=config.MINIO_ACCESS_KEY,
                      aws_secret_access_key=config.MINIO_SECRET_KEY)
    try:
        existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
        if config.MINIO_BUCKET not in existing:
            s3.create_bucket(Bucket=config.MINIO_BUCKET)
    except (BotoCoreError, ClientError) as e:
        print(f"  WARNING: MinIO not reachable ({e}). PDFs not uploaded: the CV text is in the "
              f"database anyway; rerun later with --only-cv-upload.")
        return 0

    uploaded = 0
    pairs = list(zip(cv_files["file_url"], cv_files["_pdf_path"]))
    for i, (file_url, pdf_path) in enumerate(pairs, start=1):
        key = file_url.rsplit("/", 1)[-1]
        s3.upload_file(pdf_path, config.MINIO_BUCKET, key, ExtraArgs={"ContentType": "application/pdf"})
        uploaded += 1
        if i % 200 == 0:
            print(f"  uploaded {i}/{len(cv_files)}")
    print(f"  uploaded {uploaded} PDFs")
    return uploaded


def seed_skills(engine):
    """Required skills per job title (regex rules, see job_title_skills.py)."""
    from job_title_skills import seed_job_title_skills
    seed_job_title_skills(engine)

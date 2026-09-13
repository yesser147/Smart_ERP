"""
ETL enrichment step: assigns a real resume (Kaggle Resume dataset) to
each applicant and uploads it to MinIO. Writes file_url + raw
parsed_text only -- no LLM calls, no embeddings. Those happen in
ai_engine/enrich_cv_intelligence.py, which picks up from parsed_text.

Run once after the main ETL has loaded applicants/applicant_cvs.
Needs: pip install boto3 ; MinIO running (docker compose up -d minio).
"""

import os
import pandas as pd
import boto3
from sqlalchemy import text
from load import build_engine  # reuse the ETL's existing engine/config, wherever build_engine() lives
engine = build_engine()
RESUME_CSV = r"C:\Users\yasser\Documents\stage\Smart_ERP_Core\ETL\sample_data\Resume\Resume.csv"
PDF_DIR = r"C:\Users\yasser\Documents\stage\Smart_ERP_Core\ETL\sample_data\data\data"

S3_BUCKET = "applicant-cvs"
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin123",
)


def ensure_bucket():
    existing = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if S3_BUCKET not in existing:
        s3.create_bucket(Bucket=S3_BUCKET)


def find_pdf_path(resume_id, category):
    candidate = os.path.join(PDF_DIR, str(category), f"{resume_id}.pdf")
    return candidate if os.path.exists(candidate) else None


def upload_pdf(local_path, resume_id):
    key = f"{resume_id}.pdf"
    s3.upload_file(local_path, S3_BUCKET, key)
    return f"http://localhost:9000/{S3_BUCKET}/{key}"


def run():
    ensure_bucket()
    resumes = pd.read_csv(RESUME_CSV)

    with engine.connect() as conn:
        applicants = pd.read_sql(text("SELECT applicant_id FROM applicants"), conn)

    if applicants.empty:
        print("No applicants found -- run the main ETL first.")
        return

    if len(resumes) >= len(applicants):
        sampled = resumes.sample(n=len(applicants), random_state=42).reset_index(drop=True)
    else:
        sampled = resumes.sample(n=len(applicants), replace=True, random_state=42).reset_index(drop=True)

    print(f"Assigning and uploading {len(sampled)} resumes for {len(applicants)} applicants...")

    uploaded, missing = 0, 0

    with engine.begin() as conn:
        for i, applicant_row in applicants.iterrows():
            resume = sampled.iloc[i]
            applicant_id = int(applicant_row["applicant_id"])
            resume_id, resume_text, category = resume["ID"], resume["Resume_str"], resume["Category"]

            pdf_path = find_pdf_path(resume_id, category)
            if pdf_path:
                file_url = upload_pdf(pdf_path, resume_id)
                uploaded += 1
            else:
                file_url = None
                missing += 1

            conn.execute(text("""
                UPDATE applicant_cvs SET
                    file_url = COALESCE(:file_url, file_url),
                    parsed_text = :parsed_text
                WHERE applicant_id = :applicant_id
            """), {
                "file_url": file_url,
                "parsed_text": resume_text,
                "applicant_id": applicant_id,
            })

            if (i + 1) % 50 == 0:
                print(f"  processed {i+1}/{len(applicants)}")

    print(f"Done. Uploaded {uploaded} PDFs, {missing} missing on disk (parsed_text still written for those).")


if __name__ == "__main__":
    run()
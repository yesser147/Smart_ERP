"""
Run the full ETL pipeline.

    python main.py                     # extract, clean, transform, export CSVs to output/ (database untouched)
    python main.py --load-db           # ALSO reset the database, load it, upload the resume PDFs, seed job skills
    python main.py --load-db --skip-cv-upload   # same without the MinIO upload

Sources (sample_data/): the IBM HR Analytics attrition file and the Kaggle
Resume dataset (see config.py). Settings: .env / environment variables
(DB_*, MINIO_*, ETL_*).
"""

import argparse
import os
import sys

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

import config
import extract
import clean
import transform
import load
from quality_report import DataQualityReport


def parse_args():
    p = argparse.ArgumentParser(description="Smart ERP Core -- HR ETL pipeline")
    p.add_argument("--input", default=None, help="Folder with the source files")
    p.add_argument("--output", default=None, help="Where to write the cleaned CSVs")
    p.add_argument("--load-db", action="store_true", help="Reset and load Postgres (erases the HR data!)")
    p.add_argument("--skip-schema", action="store_true", help="Don't rebuild the schema (tables already exist and are empty)")
    p.add_argument("--skip-cv-upload", action="store_true", help="Don't upload the resume PDFs to MinIO")
    return p.parse_args()


def main():
    args = parse_args()
    if args.input:
        config.INPUT_DIR = args.input
    if args.output:
        config.OUTPUT_DIR = args.output

    os.makedirs(config.REPORT_DIR, exist_ok=True)
    report = DataQualityReport()

    try:
        raw = extract.extract_all()
    except (FileNotFoundError, ValueError) as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    print("\nCLEAN")
    cleaned = {
        "employees": clean.clean_employees(raw["employees"], report),
        "resumes": clean.clean_resumes(raw["resumes"], report),
    }

    tables = transform.run_transform(cleaned, report)
    load.export_csvs(tables)

    if args.load_db:
        load.load_to_postgres(tables, apply_schema_first=not args.skip_schema)
        if not args.skip_cv_upload:
            load.upload_cv_pdfs(tables["_cv_files"])
        load.seed_skills(load.build_engine())

    report.print_summary()
    report_path = os.path.join(config.REPORT_DIR, "data_quality_report.csv")
    report.save(report_path)

    print("Pipeline finished.")
    print(f"  clean CSVs -> {config.OUTPUT_DIR}")
    print(f"  quality report -> {report_path}")
    if args.load_db:
        print("  NEXT: restart the backend so it recreates the analytics views")
        print("        (docker compose restart backend, or start it if it isn't running)")
    else:
        print("  (database not touched -- rerun with --load-db to load Postgres)")


if __name__ == "__main__":
    main()

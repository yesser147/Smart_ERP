"""
Run the full ETL pipeline.

    python main.py                    # extract, clean, transform, export CSVs to OUTPUT_DIR
    python main.py --load-db          # also load straight into Postgres (reads .env / env vars)
    python main.py --input ./mydata   # point at a different folder of the 4 Kaggle CSVs

Env vars (or a .env file, see .env.example):
    ETL_INPUT_DIR, ETL_OUTPUT_DIR, ETL_REPORT_DIR
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import argparse
import os
import sys

from dotenv import load_dotenv
load_dotenv()

import config
import extract
import clean
import transform
import load
from quality_report import DataQualityReport


def parse_args():
    p = argparse.ArgumentParser(description="Smart ERP Core -- HR ETL pipeline")
    p.add_argument("--input", default=None, help="Folder with the 4 raw Kaggle CSVs")
    p.add_argument("--output", default=None, help="Where to write cleaned CSVs + report")
    p.add_argument("--load-db", action="store_true", help="Also load directly into Postgres")
    p.add_argument("--skip-schema", action="store_true", help="Don't run schema.sql before loading (tables already exist)")
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
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # --- THE DIAGNOSTIC TEST GOES RIGHT HERE ---
    print("\n--- RAW CSV RATING CHECK ---")
    print(raw["employees"]["current_employee_rating"].value_counts(dropna=False))
    print("----------------------------\n")
    # -------------------------------------------
    

    print("\nCLEAN")
    cleaned_employees = clean.clean_employees(raw["employees"], report)
    valid_employee_ids = set(cleaned_employees["employee_id"])

    cleaned = {
        "employees": cleaned_employees,
        "trainings": clean.clean_trainings(raw["trainings"], valid_employee_ids, report),
        "recruitment": clean.clean_recruitment(raw["recruitment"], report),
        "surveys": clean.clean_surveys(raw["surveys"], valid_employee_ids, report),
    }

    tables = transform.run_transform(cleaned, report)
    print("\n--- FINAL PYTHON RATING CHECK ---")
    print(tables["employees"]["current_employee_rating"].value_counts(dropna=False))
    print("---------------------------------\n")

    load.export_csvs(tables)

    if args.load_db:
        load.load_to_postgres(tables, apply_schema_first=not args.skip_schema)

    report.print_summary()
    report_path = os.path.join(config.REPORT_DIR, "data_quality_report.csv")
    report.save(report_path)

    print("Pipeline finished.")
    print(f"  clean CSVs -> {config.OUTPUT_DIR}")
    print(f"  quality report -> {report_path}")
    if not args.load_db:
        print("  (DB not touched -- rerun with --load-db to load into Postgres)")


if __name__ == "__main__":
    main()

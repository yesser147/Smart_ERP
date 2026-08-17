# Smart ERP Core — HR ETL Pipeline

Turns the 4 raw Kaggle HR CSVs into clean, normalized, relationally-correct
data ready for your Spring Boot / PostgreSQL backend: departments, users,
roles, manager hierarchy, and (mock) applicant CVs included.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in your real Postgres credentials
```

Drop the 4 Kaggle CSVs into `sample_data/` (or point `--input` elsewhere):
`Employee_Data.csv`, `Training_and_Development_Data.csv`,
`Recruitment_Data.csv`, `Employee_Engagement_Survey_Data.csv`.

> This repo ships with `generate_test_data.py`, which creates small,
> deliberately dirty CSVs in `sample_data/` so you can see the pipeline
> work immediately. **Delete `sample_data/*.csv` before dropping in your
> real Kaggle files**, or they'll just get overwritten by the demo data
> next time you run the generator.

## Run it

```bash
python main.py                     # clean + export CSVs to output/, DB untouched
python main.py --load-db           # also creates the schema and loads Postgres directly
python main.py --input ./mydata --output ./clean_csvs
```

Every run prints a **data quality report** (also saved to
`reports/data_quality_report.csv`) listing exactly which rule fixed how
many rows in which table — nothing changes silently.

## What gets fixed automatically

- **Nulls**: missing IDs → row dropped (can't link anything to nothing);
  missing text fields → explicit `"Unknown ..."` bucket instead of blank;
  missing email → synthesized placeholder (`name.id@smarterp.local`).
- **Bad types**: unparseable dates → null; non-numeric ratings/costs/scores
  → null, then out-of-range values clipped to the configured bounds
  (`config.py`: `RATING_RANGE`, `SURVEY_SCORE_RANGE`, etc — check your real
  data's actual scale and adjust these, they're assumptions).
- **The logic bug you flagged**: `employee_status = Active` with an
  `exit_date` already in the past → the date wins, status is corrected to
  `Terminated` (see `active_with_past_exit_date_fixed` in the report).
- Other logic contradictions handled the same evidence-based way:
  `exit_date` before `start_date` (impossible → cleared), `start_date` /
  `exit_date` in the future, DOB in the future, employee younger than
  working age at hire, `Terminated` with no `exit_date` at all (flagged
  in a `needs_review` column rather than guessed).
- **Duplicates**: repeated employee/applicant IDs → first kept, rest
  dropped and counted. Duplicate emails after cleaning → de-duplicated so
  the `UNIQUE` constraint on `users.email` doesn't blow up on load.
- **Referential integrity**: trainings/surveys pointing at an
  `employee_id` that doesn't exist → dropped, not silently loaded as a
  broken FK.

## What gets built that wasn't in the raw CSVs

- **`departments`** — normalized out of `business_unit` /
  `department_type` / `division_description`.
- **`manager_id`** — the free-text `Supervisor` name is resolved to an
  actual `employee_id` (self-referencing FK). Unresolved or ambiguous
  names are flagged in the report, not guessed silently.
- **`roles` / `users`** — one login account per employee, role inferred
  from title keywords (tune the list in `transform.py::build_users`) with
  a floor of `MANAGER` for anyone who's literally someone else's manager.
  Every seeded user shares the same placeholder password hash (bcrypt of
  `Password123!`) — treat it as a "force reset on first login" seed, not
  real credentials.
- **`applicant_cvs`** — clearly-marked **mock data** (no real CVs exist in
  the Kaggle source) so your AI recruitment matching feature has
  something to query against during development.

## Files

| File | Purpose |
|---|---|
| `config.py` | Paths, column renames, drop lists, business-rule bounds — start here to tune anything |
| `extract.py` | Reads the 4 CSVs safely (encoding fallback, header whitespace) |
| `clean.py` | All the null/type/logic fixes described above |
| `transform.py` | Builds departments, manager links, roles, users, mock CVs |
| `load.py` | Exports clean CSVs always; loads straight into Postgres with `--load-db` |
| `schema.sql` | Full Postgres DDL, applied automatically before `--load-db` loads |
| `quality_report.py` | Tracks and prints/saves every fix made |
| `main.py` | Orchestrates the whole run |

## Load order (FK-safe)

`roles → departments → employees → users → trainings → engagement_surveys
→ recruitment_applicants → applicant_cvs`

`employees.manager_id` is self-referencing and declared
`DEFERRABLE INITIALLY DEFERRED` in `schema.sql`, so a manager appearing
later in the same batch than their report doesn't break the load — it's
only checked at transaction commit, and the whole load runs in one
transaction.

## Tested

This was smoke-tested end-to-end against deliberately dirty sample data,
including a real local Postgres load (schema creation + all 8 tables +
FK constraints verified afterward with a live query).

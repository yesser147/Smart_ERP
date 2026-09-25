# Smart ERP Core — HR ETL Pipeline

Builds a coherent company for the Smart ERP from two public data sets and
loads it into PostgreSQL (and the resume PDFs into MinIO).

## Sources (put them in `sample_data/`, git-ignored)

| Source | File(s) | Why |
|---|---|---|
| [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset) | `WA_Fn-UseC_-HR-Employee-Attrition.csv` | 1,470 employees simulated by IBM data scientists **with realistic relationships** between the variables (overtime, job level, stock options, satisfaction, promotions... really drive attrition: a model reaches a cross-validated AUC of 0.82) |
| [Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) | `Resume/Resume.csv` + `data/data/<CATEGORY>/<id>.pdf` | 2,484 **real resumes** (text + PDF) in 24 job categories |

The previous sources (Faker-generated Kaggle HR CSVs: random values, job
titles like "actor" in the Admin Offices, no link between satisfaction and
leaving) are no longer used.

## Setup

```powershell
python -m venv etl_env
etl_env\Scripts\pip install -r requirements.txt
copy .env.example .env          # then fill in the Postgres / MinIO credentials
```

## Run it

```powershell
etl_env\Scripts\python main.py                           # build + export CSVs to output/ (database untouched)
etl_env\Scripts\python main.py --load-db                 # ALSO reset + load Postgres, upload PDFs, seed job skills
etl_env\Scripts\python main.py --load-db --skip-cv-upload   # same without the MinIO upload
```

> **`--load-db` erases the HR tables** (employees, applicants, CVs, chats...)
> and reloads them. Only `department_budget_allocations` (backed up and
> restored by team code) and `job_title_skills` survive.
> **Afterwards restart the backend** (`docker compose restart backend`): it
> recreates the analytics views that the reset removed.

Every run prints a data quality report (also saved to `reports/data_quality_report.csv`).

## How the company is built

| What | Real / derived / generated | How |
|---|---|---|
| Employees: department, job role, level, salary, raise %, overtime, travel, commute, education, satisfaction / involvement / work-life scores, performance, trainings last year, years at company / in role / since promotion / with manager, career length, previous employers, stock options, **who left** | **real** (IBM) | one employee per IBM row |
| Hire date, exit date | derived | leavers left during the last 12 months; hire date = exit (or today) − years at company |
| Exit reason | derived | written from the leaver's own data: overtime + poor work-life balance → burnout, pay below peers → better-paid offer, no promotion for 4+ years, low satisfaction, long commute, frequent travel... |
| Teams (`departments` table) | derived | each (IBM department, job role) is split into teams of ~15 people: e.g. "Sales · Sales Executives – Team 3" (code `SL-SEX-3`). 98 teams in 3 departments |
| Managers | derived | CEO → department heads (most senior level-5 managers) → leaders (IBM "Manager" / "Research Director", level 3–4) → team members |
| Application roles | derived | CEO + department heads `ROLE_ADMIN`, HR staff level ≥ 2 `ROLE_HR_MANAGER`, other managers / research directors `ROLE_MANAGER`, others `ROLE_EMPLOYEE` |
| Titles | derived | role + level: "Junior Laboratory Technician", "Senior Sales Executive", "Sales Director", "Chief Executive Officer" |
| Salary history | derived | hire salary = current salary before the last raise, then the annual review with IBM's raise % |
| Surveys | real scores, generated date | engagement = JobInvolvement, satisfaction = JobSatisfaction, work-life = WorkLifeBalance (1–4 rescaled to 1–5) |
| Performance reviews | real rating, generated text | last annual review of each employee: rating = IBM PerformanceRating (1–5 scale), comment written from involvement, trainings, promotions and overtime; reviewer = the manager |
| Leave requests | generated | 0–3 decided requests per employee over the last year (93% approved) + about 4% of active employees with an upcoming request waiting for approval |
| Trainings | real count, generated details | as many sessions as IBM's "trainings last year"; course fits the role, cost/duration from a catalogue |
| Job openings | derived | one opening per ~6 leavers of a role, in the team that lost the most people; salary range = 25th–75th percentile of current employees in that role and level; required experience = their median career length; a template description with the role's required skills. The oldest 30% are already filled |
| Applicants | **real resumes**, generated identity | each opening receives 14–25 resumes: ~65% from a matching category (SALES → Sales Executive, HR → HR Specialist...), the rest unrelated (the AI must rank them low). Names / phones generated, emails at `example.com` so the app's emails can never reach a real person |
| Application statuses | generated | realistic funnel (applied, in review, interviewing, rejected); filled openings have one OFFERED application with a date (for time to hire) |
| Education / years of experience of applicants | left empty | read from the CV by the AI engine |

Names, emails, phone numbers and exact days are generated with a fixed seed
(`identity.py`, `config.SEED`): every run produces the same company. They are
identifiers only: no analysis uses them.

## Where the schema comes from

The ETL does not define tables. `load.apply_schema()` runs `schema.sql` (a
reset script that only DROPs), then replays the backend's Flyway migrations
`backend/src/main/resources/db/migration/V*.sql` in order, so the ETL and the
backend always build exactly the same schema.

## Files

| File | Purpose |
|---|---|
| `config.py` | paths, organisation codes, role mapping, training catalogue, recruitment settings, DB / MinIO config |
| `extract.py` | reads the IBM file and the resumes |
| `clean.py` | types, documented ranges, duplicates, impossible combinations (e.g. years at company > career length), empty resumes, missing PDFs |
| `transform.py` | builds employees, teams, managers, users, salary history, trainings, surveys, performance reviews, leave requests, openings, applicants |
| `identity.py` | generated names / emails / phones |
| `load.py` | CSV export, schema (reset + backend migrations), Postgres load, sequence sync, budget backup/restore, PDF upload, skills seed |
| `schema.sql` | reset script (DROP only) |
| `job_title_skills.py` | regex rules → required skills per job title (company roles first) |
| `quality_report.py` | logs every rule |
| `main.py` | orchestrates the run |

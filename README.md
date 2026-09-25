# Smart ERP Core (Nexus ERP)

HR ERP with KPI dashboards, an AI layer (HR chatbot, CV reading with an LLM,
candidate/job matching, candidate chat) and ML predictions (attrition risk,
training budget advisor). Full technical description: `RAPPORT.docx`.
Known limits and next steps: `FUTURE_IMPROVEMENTS.txt`.

**What the application does**

| Area | Pages |
|---|---|
| Analytics | Overview, Turnover (with retention curves), Compensation & performance, Recruitment & training (funnel, time to hire) |
| People | Employees (CSV and payroll export), employee file (AI flight-risk card, performance reviews), Departments, Leave requests |
| Recruitment | Job openings (create one with an AI-written description), candidates ranked by AI, Applicants (batch CV analysis), CV search, interview questions, offer and hire |
| AI & strategy | Budget advisor (what-if simulator, approve an allocation), Retention strategy (printable), HR chatbot (bottom right) |
| Administration | Users & roles, Audit log, AI models (quality + retrain) |
| Self-service | My space: an employee's own file, reviews and leave requests |
| Public | Careers site at http://localhost:4200/careers (no login): open jobs and the application form |

Everything runs in Docker except the ETL (the data loader), which you run by
hand only when the data must be (re)loaded.

**Data**: the company is built from the [IBM HR Analytics](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset)
data set (1,470 employees, simulated by IBM with realistic relationships between the variables) and the
applicants from the [Kaggle Resume dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)
(real resumes). What is real, derived or generated is listed in `ETL/README.md`.

| Part | Container | URL / port |
|---|---|---|
| Frontend (Angular + nginx) | `smart_erp_frontend` | http://localhost:4200 |
| Backend API (Spring Boot) | `smart_erp_backend` | http://localhost:8080/api/v1 |
| AI API (FastAPI) | `smart_erp_ai_engine` | http://localhost:8000/api/ai (this PC only) |
| Database (PostgreSQL + pgvector) | `smart_erp_db` | localhost:5432 |
| DB admin (pgAdmin) | `smart_erp_pgadmin` | http://localhost:5050 |
| CV storage (MinIO, private bucket) | `smart_erp_minio` | http://localhost:9001 (console) |
| ETL | — (Python on your PC) | `ETL/` |

---

## 1. Prerequisites (install once)

- **Docker Desktop** (running)
- **Python 3.11** — only for the ETL
- **Ollama** with `llama3.1` (`ollama pull llama3.1`), running on your PC — local LLM
- A **Groq API key** (console.groq.com) — cloud LLM, used first by default
- A **Gmail app password** for the sending account (see `RAPPORT.docx` / Google account > Security > App passwords)

Java, Maven and Node are **not** needed on your PC anymore: they are inside the images.

## 2. Configuration files (once)

Secrets are never committed. Copy each template and fill it in:

| Copy | To | What to fill |
|---|---|---|
| `.env.example` | `.env` | Postgres / pgAdmin / MinIO passwords (Docker) |
| `backend/.env.example` | `backend/.env` | DB password, Gmail, `JWT_SECRET`, `AI_DB_PASSWORD`, MinIO |
| `ai_engine/.env.example` | `ai_engine/.env` | DB password, `AI_DB_PASSWORD`, `JWT_SECRET`, Groq key, MinIO |
| `ETL/.env.example` | `ETL/.env` | DB password, MinIO |

Values that **must be identical**:

- `JWT_SECRET` in `backend/.env` and `ai_engine/.env`
- `AI_DB_PASSWORD` in `backend/.env` and `ai_engine/.env`
- Postgres password: `POSTGRES_PASSWORD` in `.env` = `DB_PASSWORD` in the three other files
- MinIO password: `MINIO_ROOT_PASSWORD` in `.env` = `MINIO_SECRET_KEY` in the three other files

You don't need to change `DB_HOST` / `MINIO_ENDPOINT` in the `.env` files:
docker-compose sets the right values for the containers, and the ETL uses `localhost`.

Generate a `JWT_SECRET`:

```powershell
python -c "import secrets,base64;print(base64.b64encode(secrets.token_bytes(64)).decode())"
```

On this machine the four `.env` files already exist and are filled in.

## 3. Start / stop the application

Start everything (the first time, building the images takes 10–20 minutes):

```powershell
docker compose up -d --build
```

Wait about 30 seconds, then open http://localhost:4200 and log in with
`admin@smarterp.com` / `Admin@123456`. Keep the Ollama app running.

| Action | Command |
|---|---|
| See what is running | `docker compose ps` |
| Follow the backend logs | `docker compose logs -f backend` |
| Follow the AI engine logs | `docker compose logs -f ai-engine` |
| Restart one service | `docker compose restart backend` |
| Rebuild after a code change | `docker compose up -d --build` |
| Stop everything (data is kept) | `docker compose down` |

`docker compose down -v` would ALSO delete the database and the CV files. Don't use `-v` unless you mean it.

## 4. Load the data with the ETL (first installation or full reload)

> **`main.py --load-db` erases the HR data** (employees, applicants, processed CVs, hires, chats)
> and reloads it from the source files. Back up the database first (section 6).

**4.1 — Once: download the two data sources into `ETL/sample_data/`** (git-ignored)

| Source | Where to put it |
|---|---|
| [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset) — 1,470 employees | `ETL/sample_data/WA_Fn-UseC_-HR-Employee-Attrition.csv` |
| [Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) — 2,484 real resumes | `ETL/sample_data/Resume/Resume.csv` and the PDFs in `ETL/sample_data/data/data/<CATEGORY>/<id>.pdf` |

**4.2 — Once: create the ETL's Python environment**

```powershell
cd ETL
python -m venv etl_env
etl_env\Scripts\pip install -r requirements.txt
cd ..
```

**4.3 — Start the database and MinIO**

```powershell
docker compose up -d postgres minio
```

**4.4 — Run the ETL** (one command: builds the company, loads the database, uploads the resume PDFs to MinIO, seeds the required skills per job)

```powershell
cd ETL
etl_env\Scripts\python main.py --load-db
cd ..
```

It takes about a minute and ends with `Pipeline finished.` It loads 1,470 employees in 98 teams,
42 job openings and about 800 applicants with real resumes. The data quality report is printed and saved
in `ETL/reports/data_quality_report.csv`.

**4.5 — Start (or restart) the application**: the backend recreates the views the reload removed

```powershell
docker compose up -d --build
docker compose restart backend
```

**4.6 — Let the LLM read the CVs.** Candidates only appear in the AI ranking once their CV has been read.
Three ways, choose one:

- a job opening: the page shows "X of Y CVs analysed" and an **Analyse N CV(s)** button (a few seconds per CV);
- Recruitment > **Applicants** > **Analyse N pending CV(s)** (all of them, the page must stay open);
- all at once from the command line (about 5 s per CV with Ollama; `Ctrl+C` stops it, running it again continues):

```powershell
docker compose exec -e LLM_PROVIDER=ollama ai-engine python -m models.recruitment.enrich_cv_intelligence
```

Applications sent from the careers page are analysed automatically.

**4.7 — Models**: the trained models in the repository match this data. To retrain after a data change:
Administration > **AI models** > **Retrain models** (as an administrator), or:

```powershell
docker compose exec ai-engine python -m models.retention.train
docker compose exec ai-engine python -m models.budget_advisor.train
docker compose restart ai-engine
```

## 5. Quick test after starting

1. http://localhost:4200 → log in → the Overview page shows the KPIs and a "High flight risk" number.
2. The AI button (bottom right) → a frequent question → an answer with a table and a chart.
3. Recruitment > Job openings → a job → "Analyse CVs" if needed → ranked candidates.
4. A candidate → the AI assistant answers; the "Interview questions" tab prepares the interview.
5. People > Leave requests → approve one: the badge in the sidebar goes down.
6. http://localhost:4200/careers → the public job board.
7. `docker compose ps` → all services `Up`.

## 6. Back up and restore the database

Back up (keep the file outside the project folder):

```powershell
docker exec smart_erp_db pg_dump -U postgres -d smart_erp -F c -f /tmp/backup.dump
docker cp smart_erp_db:/tmp/backup.dump C:\Users\yasser\Documents\stage\backups\smart_erp.dump
```

Restore (replaces the current database):

```powershell
docker compose stop backend ai-engine
docker cp C:\Users\yasser\Documents\stage\backups\smart_erp.dump smart_erp_db:/tmp/old.dump
docker exec smart_erp_db psql -U postgres -d postgres -c "DROP DATABASE smart_erp WITH (FORCE);"
docker exec smart_erp_db psql -U postgres -d postgres -c "CREATE DATABASE smart_erp;"
docker exec smart_erp_db pg_restore -U postgres -d smart_erp /tmp/old.dump
docker compose start backend ai-engine
```

## 7. Running without Docker (development)

Still possible: stop the app containers (`docker compose stop backend ai-engine frontend`), then

```powershell
cd backend;   .\mvnw spring-boot:run            # needs Java 21
cd ai_engine; venv\Scripts\python main_api.py   # needs the venv: python -m venv venv; venv\Scripts\pip install -r requirements.txt
cd frontend;  npm install; npm start            # needs Node 18+
```

AI engine unit tests: `cd ai_engine; venv\Scripts\python -m unittest discover -s tests -v`

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `docker compose up` says "set POSTGRES_PASSWORD in .env" | the root `.env` is missing: copy `.env.example` |
| `smart_erp_backend` keeps restarting | `docker compose logs backend`: usually a missing value in `backend/.env` (JWT_SECRET, MAIL_PASSWORD, DB_PASSWORD, AI_DB_PASSWORD) |
| The app goes back to the login page | the session expired or the JWT secret changed: log in again |
| AI pages: 401 "Invalid or expired session." | `JWT_SECRET` differs between `backend/.env` and `ai_engine/.env` |
| Dashboard empty after an ETL reload | the views are missing: `docker compose restart backend` |
| Chatbot: "password authentication failed for ai_readonly_user" | `AI_DB_PASSWORD` differs between the two `.env` files and the database role |
| "Analyse CV": "Could not read the PDF" / 403 | wrong `MINIO_SECRET_KEY` in `ai_engine/.env` |
| AI features: "AI unavailable" | no Groq key / quota, and Ollama is not running on the PC |
| Emails are not sent | wrong Gmail app password in `backend/.env` (`docker compose logs backend` shows "Could not send the ... email") |
| A page stays on its loading placeholders in a background tab | the browser pauses hidden tabs: bring the tab to the front |
| ETL-created employees can't log in | expected: their accounts have no password and fictitious e-mail addresses. To demo the employee view, apply on the careers page with an e-mail address you own, then hire yourself: the activation e-mail lets you choose a password |
| Port 8080 / 8000 / 4200 already in use | a `mvnw` / `python main_api.py` / `npm start` is still running: stop it |

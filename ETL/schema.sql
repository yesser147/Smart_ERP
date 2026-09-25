-- ETL reset script: empties the database before a full reload.
-- It only DROPS. The tables are then created by the backend's Flyway
-- migrations (backend/src/main/resources/db/migration/V*.sql), which
-- load.py replays in order, so the ETL and the backend always build the
-- exact same schema (see load.apply_schema).

DROP TABLE IF EXISTS application_status_history CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS leave_requests CASCADE;
DROP TABLE IF EXISTS performance_reviews CASCADE;
DROP TABLE IF EXISTS ai_chat_messages CASCADE;
DROP TABLE IF EXISTS ai_query_logs CASCADE;
DROP TABLE IF EXISTS applicant_cvs CASCADE;
DROP TABLE IF EXISTS job_applications CASCADE;
DROP TABLE IF EXISTS job_postings CASCADE;
DROP TABLE IF EXISTS applicants CASCADE;
DROP TABLE IF EXISTS engagement_surveys CASCADE;
DROP TABLE IF EXISTS employee_trainings CASCADE;
DROP TABLE IF EXISTS training_courses CASCADE;
DROP TABLE IF EXISTS salary_history CASCADE;
DROP TABLE IF EXISTS user_tokens CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- department_budget_allocations holds app data, not CSV data. load.py backs
-- it up BEFORE this script runs and restores it after the reload, so it is
-- dropped here (otherwise the restore would duplicate its rows).
DROP TABLE IF EXISTS department_budget_allocations CASCADE;

-- job_title_skills is NOT dropped: it holds the curated / LLM-cached
-- required skills per job title and has no foreign keys.

-- Dropping the tables also dropped the analytics views (CASCADE). Removing
-- Flyway's history makes the backend recreate them (R__create_bi_views.sql)
-- on its next start.
DROP TABLE IF EXISTS flyway_schema_history CASCADE;

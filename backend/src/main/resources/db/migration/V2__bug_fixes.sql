-- Bug-fix migration. Every statement is idempotent: it runs on a database
-- built by the old code (upgrade) and again after each ETL reset (no-op).

-- 1. Columns the AI engine writes to (were only added by a Python script before)
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS ai_match_reasoning TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS ai_embedding_score NUMERIC(5,1);
ALTER TABLE applicant_cvs ADD COLUMN IF NOT EXISTS experience_profile TEXT;
ALTER TABLE applicant_cvs ADD COLUMN IF NOT EXISTS cv_years_of_experience NUMERIC;

-- 2. When the application status last changed (interview / offer / reject):
--    needed for a real "time to hire" (offer date - application date)
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP;

-- 3. Real cost and duration of each training session (the catalog only
--    keeps one reference value per program)
ALTER TABLE employee_trainings ADD COLUMN IF NOT EXISTS cost NUMERIC(10, 2);
ALTER TABLE employee_trainings ADD COLUMN IF NOT EXISTS duration_days NUMERIC;

-- 4. Table behind the AiQueryLog entity (Hibernate validation failed without it)
CREATE TABLE IF NOT EXISTS ai_query_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    response TEXT,
    execution_time_ms BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 5. Candidate chat history (was kept in the AI engine's memory and lost on restart)
CREATE TABLE IF NOT EXISTS ai_chat_messages (
    id BIGSERIAL PRIMARY KEY,
    applicant_id BIGINT NOT NULL,
    job_id BIGINT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ai_chat_messages_session ON ai_chat_messages(applicant_id, job_id, id);

-- 6. Role names must match the Java RoleName enum. Old ETL runs created
--    ROLE_SUPER_ADMIN and ROLE_USER, which Hibernate can't load.
--    a) the target role already exists (added by DatabaseSeeder): move users, drop the old role
UPDATE users SET role_id = (SELECT id FROM roles WHERE name = 'ROLE_ADMIN')
WHERE role_id = (SELECT id FROM roles WHERE name = 'ROLE_SUPER_ADMIN')
  AND EXISTS (SELECT 1 FROM roles WHERE name = 'ROLE_ADMIN');
DELETE FROM roles WHERE name = 'ROLE_SUPER_ADMIN'
  AND EXISTS (SELECT 1 FROM roles WHERE name = 'ROLE_ADMIN');

UPDATE users SET role_id = (SELECT id FROM roles WHERE name = 'ROLE_EMPLOYEE')
WHERE role_id = (SELECT id FROM roles WHERE name = 'ROLE_USER')
  AND EXISTS (SELECT 1 FROM roles WHERE name = 'ROLE_EMPLOYEE');
DELETE FROM roles WHERE name = 'ROLE_USER'
  AND EXISTS (SELECT 1 FROM roles WHERE name = 'ROLE_EMPLOYEE');

--    b) the target role doesn't exist yet: just rename
UPDATE roles SET name = 'ROLE_ADMIN' WHERE name = 'ROLE_SUPER_ADMIN';
UPDATE roles SET name = 'ROLE_EMPLOYEE' WHERE name = 'ROLE_USER';

-- 7. Random placeholder match scores written by old ETL runs look like real
--    AI results to the matcher. Scores computed by the AI always come with
--    a reasoning, so clear only the ones without one.
UPDATE job_applications SET ai_match_score = NULL
WHERE ai_match_score IS NOT NULL AND ai_match_reasoning IS NULL;

-- 8. Id sequences the ETL left behind its bulk-loaded ids: the next row
--    created by the app would reuse an existing id (duplicate key error).
SELECT setval(pg_get_serial_sequence('applicants', 'applicant_id'),
              GREATEST((SELECT COALESCE(MAX(applicant_id), 1) FROM applicants), 1));
SELECT setval(pg_get_serial_sequence('employees', 'employee_id'),
              GREATEST((SELECT COALESCE(MAX(employee_id), 1) FROM employees), 1));

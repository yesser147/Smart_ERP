CREATE EXTENSION IF NOT EXISTS vector;

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
DROP TABLE IF EXISTS flyway_schema_history CASCADE;
-- NOTE: department_budget_allocations is NOT in this DROP list on purpose.
-- It holds live data written by the Spring Boot app (confirmed budget
-- allocations), not data sourced from the Kaggle CSVs. Dropping departments
-- CASCADE below will still take it down if it already exists, because it
-- has a FK to departments -- see load.py's backup_budget_allocations() /
-- restore_budget_allocations() for how reruns preserve it anyway.

-- 1. Security & Governance
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY, 
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS departments (
    department_id BIGSERIAL PRIMARY KEY,
    business_unit VARCHAR(255),
    department_type VARCHAR(255),
    division_description VARCHAR(255),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Core Workforce & Analytics
CREATE TABLE IF NOT EXISTS employees (
    employee_id BIGINT PRIMARY KEY,
    department_id BIGINT REFERENCES departments(department_id),
    manager_id BIGINT REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    start_date DATE,
    exit_date DATE,
    title VARCHAR(150),
    employee_status VARCHAR(50),
    employee_type VARCHAR(50),
    employee_classification_type VARCHAR(50),
    termination_type VARCHAR(100),
    termination_description TEXT,
    dob DATE,
    state VARCHAR(50),
    job_function VARCHAR(255),
    gender VARCHAR(20),
    location VARCHAR(50),
    performance_score VARCHAR(50),
    current_employee_rating NUMERIC,
    salary NUMERIC(12, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    needs_review BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE SEQUENCE IF NOT EXISTS employees_employee_id_seq OWNED BY employees.employee_id;
ALTER TABLE employees ALTER COLUMN employee_id SET DEFAULT nextval('employees_employee_id_seq');

CREATE TABLE IF NOT EXISTS salary_history (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT REFERENCES employees(employee_id) ON DELETE CASCADE,
    effective_date DATE NOT NULL,
    salary NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    change_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Spring Security & Tokens
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    employee_id BIGINT REFERENCES employees(employee_id) UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    role_id BIGINT REFERENCES roles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) DEFAULT 'SYSTEM',
    updated_by VARCHAR(255) DEFAULT 'SYSTEM'
);

CREATE TABLE IF NOT EXISTS user_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    token_type VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Learning & Engagement
CREATE TABLE IF NOT EXISTS training_courses (
    course_id BIGSERIAL PRIMARY KEY,
    program_name VARCHAR(255) UNIQUE NOT NULL,
    training_type VARCHAR(100),
    trainer VARCHAR(150),
    duration_days NUMERIC,
    cost NUMERIC(10, 2),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS employee_trainings (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT REFERENCES employees(employee_id) ON DELETE CASCADE,
    course_id BIGINT REFERENCES training_courses(course_id),
    training_date DATE NOT NULL,
    completion_status VARCHAR(50),
    location VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS engagement_surveys (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT REFERENCES employees(employee_id),
    survey_date DATE,
    engagement_score NUMERIC,
    satisfaction_score NUMERIC,
    work_life_balance_score NUMERIC
);

-- 5. ATS & AI Recruitment
CREATE TABLE IF NOT EXISTS applicants (
    applicant_id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(50),
    education_level VARCHAR(100),
    years_of_experience NUMERIC,
    gender VARCHAR(20),
    dob DATE,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(50),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_postings (
    job_id BIGSERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    department_id BIGINT REFERENCES departments(department_id),
    location VARCHAR(100),
    required_experience_years NUMERIC,
    offered_salary_min NUMERIC(12, 2),
    offered_salary_max NUMERIC(12, 2),
    status VARCHAR(50) DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_applications (
    application_id UUID PRIMARY KEY,
    applicant_id BIGINT REFERENCES applicants(applicant_id) ON DELETE CASCADE,
    job_id BIGINT REFERENCES job_postings(job_id),
    application_date DATE NOT NULL,
    desired_salary NUMERIC(12, 2),
    status VARCHAR(50) DEFAULT 'APPLIED',
    ai_match_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applicant_cvs (
    id UUID PRIMARY KEY,
    applicant_id BIGINT REFERENCES applicants(applicant_id) ON DELETE CASCADE UNIQUE,
    file_url VARCHAR(255),
    parsed_text TEXT,
    extracted_skills_json JSONB,
    cv_embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. AI Budget Advisor: confirmed allocations (app-owned, not ETL-sourced)
CREATE TABLE IF NOT EXISTS department_budget_allocations (
    id BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(department_id),
    allocated_budget NUMERIC(12, 2) NOT NULL,
    predicted_performance NUMERIC(6, 3),
    approved_by UUID REFERENCES users(id),
    fiscal_period VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Query Performance & Vectors
CREATE INDEX IF NOT EXISTS idx_emp_dept ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_emp_status ON employees(employee_status);
CREATE INDEX IF NOT EXISTS idx_emp_manager ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_emp_salary ON employees(salary);
CREATE INDEX IF NOT EXISTS idx_tokens_user ON user_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_tokens_lookup ON user_tokens(token, token_type);
CREATE INDEX IF NOT EXISTS idx_salary_hist_emp ON salary_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_emp_trainings_emp ON employee_trainings(employee_id);
CREATE INDEX IF NOT EXISTS idx_emp_trainings_course ON employee_trainings(course_id);
CREATE INDEX IF NOT EXISTS idx_job_apps_applicant ON job_applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_job_apps_job ON job_applications(job_id);
CREATE INDEX IF NOT EXISTS idx_surveys_emp ON engagement_surveys(employee_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_budget_alloc_dept ON department_budget_allocations(department_id, created_at DESC);
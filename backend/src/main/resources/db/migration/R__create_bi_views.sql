-- =============================================================================
-- 1. Department Turnover & Closure Analytics
-- =============================================================================

CREATE OR REPLACE VIEW v_closed_departments AS
SELECT 
    d.department_id,
    d.business_unit,
    COUNT(e.employee_id) AS total_historical_employees,
    SUM(CASE WHEN UPPER(e.employee_status) LIKE '%TERMINATED%' THEN 1 ELSE 0 END) AS total_terminated_employees,
    MAX(e.exit_date) AS estimated_closure_date
FROM departments d
JOIN employees e ON d.department_id = e.department_id
WHERE e.is_deleted = FALSE
GROUP BY 
    d.department_id, 
    d.business_unit
HAVING 
    SUM(CASE WHEN UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE') THEN 1 ELSE 0 END) = 0
    AND SUM(CASE WHEN UPPER(e.employee_status) LIKE '%TERMINATED%' THEN 1 ELSE 0 END) > 0;


CREATE OR REPLACE VIEW v_department_turnover AS
SELECT 
    d.department_id,
    d.business_unit,
    COUNT(e.employee_id) AS total_employees,
    SUM(CASE 
        WHEN UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE') 
             AND (e.start_date IS NULL OR e.start_date <= CURRENT_DATE) 
        THEN 1 ELSE 0 
    END) AS active_count,
    SUM(CASE 
        WHEN UPPER(e.employee_status) LIKE '%TERMINATED%' 
        THEN 1 ELSE 0 
    END) AS terminated_count,
    COALESCE(
        ROUND(
            SUM(CASE WHEN UPPER(e.employee_status) LIKE '%TERMINATED%' THEN 1 ELSE 0 END) * 100.0 / 
            NULLIF(COUNT(e.employee_id), 0), 2
        ), 
        0.00
    ) AS turnover_rate_pct
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id 
    AND UPPER(COALESCE(e.employee_status, '')) != 'FUTURE START'
    AND e.is_deleted = FALSE
GROUP BY 
    d.department_id, 
    d.business_unit;


CREATE OR REPLACE VIEW v_department_type_turnover AS
SELECT 
    d.department_type,
    COUNT(e.employee_id) AS total_employees,
    SUM(CASE 
        WHEN UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE') 
             AND (e.start_date IS NULL OR e.start_date <= CURRENT_DATE) 
        THEN 1 ELSE 0 
    END) AS active_count,
    SUM(CASE 
        WHEN UPPER(e.employee_status) LIKE '%TERMINATED%' 
        THEN 1 ELSE 0 
    END) AS terminated_count,
    COALESCE(
        ROUND(
            SUM(CASE WHEN UPPER(e.employee_status) LIKE '%TERMINATED%' THEN 1 ELSE 0 END) * 100.0 / 
            NULLIF(COUNT(e.employee_id), 0), 2
        ), 
        0.00
    ) AS turnover_rate_pct
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id 
    AND UPPER(COALESCE(e.employee_status, '')) != 'FUTURE START'
    AND e.is_deleted = FALSE
GROUP BY 
    d.department_type;


-- =============================================================================
-- 2. Employee Performance & Survey Engagement Metrics
-- =============================================================================

CREATE OR REPLACE VIEW v_employee_performance_engagement AS
SELECT 
    e.employee_id,
    e.department_id,
    e.job_function,
    e.title,
    e.performance_score,
    ROUND(AVG(es.engagement_score), 2) AS avg_engagement_score,
    ROUND(AVG(es.satisfaction_score), 2) AS avg_satisfaction_score,
    ROUND(AVG(es.work_life_balance_score), 2) AS avg_work_life_balance
FROM employees e
LEFT JOIN engagement_surveys es ON e.employee_id = es.employee_id
WHERE e.is_deleted = FALSE
GROUP BY 
    e.employee_id, 
    e.department_id, 
    e.job_function, 
    e.title, 
    e.performance_score;


-- =============================================================================
-- 3. Salary Distribution & Compensation Equity
-- =============================================================================

CREATE OR REPLACE VIEW v_salary_distribution AS
SELECT 
    d.department_id,
    d.business_unit,
    e.job_function,
    COUNT(e.employee_id) AS employee_count,
    ROUND(AVG(e.salary), 2) AS avg_salary,
    MIN(e.salary) AS min_salary,
    MAX(e.salary) AS max_salary,
    SUM(e.salary) AS total_payroll_burden
FROM departments d
JOIN employees e ON d.department_id = e.department_id
WHERE UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE') 
  AND e.is_deleted = FALSE
GROUP BY d.department_id, d.business_unit, e.job_function;


-- =============================================================================
-- 4. Recruitment Funnel & ATS Performance
-- =============================================================================

CREATE OR REPLACE VIEW v_recruitment_funnel_ats AS
SELECT 
    jp.job_id,
    jp.title AS job_title,
    jp.department_id,
    jp.status AS posting_status,
    jp.offered_salary_min,
    jp.offered_salary_max,
    COUNT(ja.application_id) AS total_applications,
    SUM(CASE WHEN UPPER(ja.status) = 'APPLIED' THEN 1 ELSE 0 END) AS applied_count,
    SUM(CASE WHEN UPPER(ja.status) = 'IN REVIEW' THEN 1 ELSE 0 END) AS in_review_count,
    SUM(CASE WHEN UPPER(ja.status) = 'INTERVIEWING' THEN 1 ELSE 0 END) AS interviewing_count,
    SUM(CASE WHEN UPPER(ja.status) = 'OFFERED' THEN 1 ELSE 0 END) AS offered_count,
    SUM(CASE WHEN UPPER(ja.status) = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_count,
    ROUND(AVG(ja.desired_salary), 2) AS avg_desired_salary,
    ROUND(AVG(ja.ai_match_score), 2) AS avg_ai_match_score
FROM job_postings jp
LEFT JOIN job_applications ja ON jp.job_id = ja.job_id
GROUP BY 
    jp.job_id, 
    jp.title, 
    jp.department_id, 
    jp.status, 
    jp.offered_salary_min, 
    jp.offered_salary_max;

-- =============================================================================
-- 5. Training & Upskilling Analytics
-- =============================================================================

CREATE OR REPLACE VIEW v_training_analytics AS
SELECT 
    d.department_id,
    d.business_unit,
    COUNT(DISTINCT et.employee_id) AS trained_employees_count,
    COUNT(et.id) AS total_trainings_completed,
    COALESCE(SUM(tc.cost), 0.00) AS total_training_investment,
    ROUND(AVG(tc.duration_days), 1) AS avg_course_duration_days
FROM departments d
JOIN employees e ON d.department_id = e.department_id
JOIN employee_trainings et ON e.employee_id = et.employee_id
JOIN training_courses tc ON et.course_id = tc.course_id
WHERE UPPER(et.completion_status) = 'COMPLETED'
  AND e.is_deleted = FALSE
GROUP BY d.department_id, d.business_unit;


-- =============================================================================
-- 6. Flight Risk & Attrition Indicators (Feeds ML Engine)
-- =============================================================================

CREATE OR REPLACE VIEW v_attrition_risk_indicators AS
SELECT 
    e.employee_id,
    e.department_id,
    e.job_function,
    e.title,
    e.performance_score,
    e.salary,
    e.start_date,
    ROUND(AVG(es.engagement_score), 2) AS recent_engagement,
    ROUND(AVG(es.satisfaction_score), 2) AS recent_satisfaction,
    ROUND(AVG(es.work_life_balance_score), 2) AS recent_wlb,
    CASE 
        WHEN AVG(es.satisfaction_score) < 2.5 OR AVG(es.engagement_score) < 2.5 THEN 'HIGH'
        WHEN AVG(es.satisfaction_score) < 3.5 OR AVG(es.work_life_balance_score) < 2.5 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS heuristic_risk_level
FROM employees e
LEFT JOIN engagement_surveys es ON e.employee_id = es.employee_id
WHERE UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE') 
  AND e.is_deleted = FALSE
GROUP BY 
    e.employee_id, 
    e.department_id, 
    e.job_function, 
    e.title, 
    e.performance_score, 
    e.salary, 
    e.start_date;


-- =============================================================================
-- 7. Top Performer Benchmarks (Feeds ATS Matching Engine)
-- =============================================================================

CREATE OR REPLACE VIEW v_top_performer_benchmarks AS
SELECT 
    e.employee_id,
    e.department_id,
    e.job_function,
    e.title,
    e.performance_score,
    e.gender,
    ROUND(AVG(es.engagement_score), 2) AS avg_engagement
FROM employees e
JOIN engagement_surveys es ON e.employee_id = es.employee_id
WHERE UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE') 
  AND e.is_deleted = FALSE
  AND UPPER(e.performance_score) LIKE '%EXCEEDS%'
GROUP BY 
    e.employee_id, 
    e.department_id, 
    e.job_function, 
    e.title, 
    e.performance_score, 
    e.gender;


-- =============================================================================
-- 8. AI Feature Views (Retention, Exit Reasons, Training Budgets)
-- =============================================================================

CREATE OR REPLACE VIEW v_ai_retention_features AS
SELECT
    e.employee_id,
    e.department_id,
    d.business_unit,
    e.job_function,
    e.performance_score,
    e.salary,
    e.start_date,
    e.gender,
    e.employee_status,
    e.is_deleted,
    AVG(es.engagement_score) AS avg_engagement_score,
    AVG(es.satisfaction_score) AS avg_satisfaction_score,
    AVG(es.work_life_balance_score) AS avg_work_life_balance,
    dt.turnover_rate_pct AS department_turnover_rate
FROM employees e
JOIN departments d ON d.department_id = e.department_id
LEFT JOIN engagement_surveys es ON es.employee_id = e.employee_id
LEFT JOIN v_department_turnover dt ON dt.department_id = e.department_id
WHERE e.is_deleted = FALSE
GROUP BY
    e.employee_id, e.department_id, d.business_unit, e.job_function,
    e.performance_score, e.salary, e.start_date, e.gender,
    e.employee_status, e.is_deleted, dt.turnover_rate_pct;


DROP VIEW IF EXISTS v_ai_exit_reason_frequencies CASCADE;
CREATE OR REPLACE VIEW v_ai_exit_reason_frequencies AS
SELECT 
    e.department_id,
    d.department_type,
    e.termination_description,
    COUNT(*) AS exit_count
FROM employees e
JOIN departments d ON d.department_id = e.department_id
WHERE UPPER(e.employee_status) LIKE '%TERMINATED%' 
  AND e.termination_description IS NOT NULL
  AND e.is_deleted = FALSE
GROUP BY e.department_id, d.department_type, e.termination_description;


DROP VIEW IF EXISTS v_ai_training_budget_features CASCADE;
CREATE OR REPLACE VIEW v_ai_training_budget_features AS
SELECT 
    d.department_id,
    d.business_unit,
    d.department_type,
    COALESCE(ta.total_training_investment, 0.00) AS training_budget,
    COUNT(DISTINCT e.employee_id) AS headcount,
    COALESCE(ROUND(AVG(e.current_employee_rating), 2), 3.00) AS avg_performance,
    COALESCE(ROUND(AVG(es.engagement_score), 2), 3.00) AS avg_engagement,
    COALESCE(dt.turnover_rate_pct, 0.00) AS department_turnover_rate
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id 
    AND e.is_deleted = FALSE 
    AND UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE')
LEFT JOIN v_training_analytics ta ON d.department_id = ta.department_id
LEFT JOIN engagement_surveys es ON e.employee_id = es.employee_id
LEFT JOIN v_department_turnover dt ON dt.department_id = d.department_id
GROUP BY 
    d.department_id, d.business_unit, d.department_type, ta.total_training_investment, dt.turnover_rate_pct;

    CREATE OR REPLACE VIEW v_gender_pay_gap AS
SELECT 
    d.business_unit,
    e.gender,
    ROUND(AVG(e.salary), 2) AS avg_salary,
    COUNT(*) AS employee_count
FROM employees e
JOIN departments d ON d.department_id = e.department_id
WHERE UPPER(e.employee_status) IN ('ACTIVE', 'ON LEAVE') AND e.is_deleted = FALSE
GROUP BY d.business_unit, e.gender;

CREATE OR REPLACE VIEW v_time_to_hire AS
SELECT
    jp.job_id,
    jp.title AS job_title,
    jp.department_id,
    ROUND(AVG(ja.application_date - jp.created_at::date), 1) AS avg_days_to_hire,
    COUNT(*) FILTER (WHERE UPPER(ja.status) = 'OFFERED') AS hired_count
FROM job_postings jp
JOIN job_applications ja ON ja.job_id = jp.job_id
WHERE UPPER(ja.status) = 'OFFERED'
GROUP BY jp.job_id, jp.title, jp.department_id;
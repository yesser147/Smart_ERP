CREATE OR REPLACE VIEW v_department_turnover AS
SELECT 
    d.department_id,
    d.business_unit,
    COUNT(e.employee_id) AS total_employees,
    SUM(CASE WHEN e.employee_status = 'Active' AND e.start_date <= CURRENT_DATE THEN 1 ELSE 0 END) AS active_count,
    SUM(CASE WHEN e.employee_status = 'Terminated' THEN 1 ELSE 0 END) AS terminated_count,
    ROUND(
        SUM(CASE WHEN e.employee_status = 'Terminated' THEN 1 ELSE 0 END) * 100.0 / 
        NULLIF(COUNT(e.employee_id), 0), 2
    ) AS turnover_rate_pct
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id 
    AND e.employee_status != 'Future Start'
GROUP BY 
    d.department_id, 
    d.business_unit;

-- 2. Employee Performance & Survey Engagement Metrics
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


-- 3. Salary Distribution & Compensation Equity
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
WHERE e.employee_status = 'Active' AND e.is_deleted = FALSE
GROUP BY d.department_id, d.business_unit, e.job_function;


-- 4. Recruitment Funnel & ATS Performance
CREATE OR REPLACE VIEW v_recruitment_funnel_ats AS
SELECT 
    jp.job_id,
    jp.title AS job_title,
    jp.department_id,
    jp.status AS posting_status,
    jp.offered_salary_min,
    jp.offered_salary_max,
    COUNT(ja.application_id) AS total_applications,
    SUM(CASE WHEN ja.status = 'APPLIED' THEN 1 ELSE 0 END) AS pending_applications,
    SUM(CASE WHEN ja.status = 'HIRED' THEN 1 ELSE 0 END) AS hired_count,
    SUM(CASE WHEN ja.status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_count,
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


-- 5. Training & Upskilling Analytics
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
WHERE et.completion_status = 'Completed'
GROUP BY d.department_id, d.business_unit;


-- 6. Flight Risk & Attrition Indicators (Feeds Python ML Model)
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
WHERE e.employee_status = 'Active' AND e.is_deleted = FALSE
GROUP BY 
    e.employee_id, 
    e.department_id, 
    e.job_function, 
    e.title, 
    e.performance_score, 
    e.salary, 
    e.start_date;


-- 7. Top Performer Benchmarks (Feeds Python ATS Matching Engine)
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
WHERE e.employee_status = 'Active' 
  AND e.performance_score = 'Exceeds'
GROUP BY 
    e.employee_id, 
    e.department_id, 
    e.job_function, 
    e.title, 
    e.performance_score, 
    e.gender;
-- Detailed employee attributes from the IBM HR Analytics data set.
-- They are the real drivers of attrition used by the retention model and
-- shown on the employee page. Idempotent (runs again after an ETL reset).

ALTER TABLE employees ADD COLUMN IF NOT EXISTS job_level INT;                  -- 1 (junior) .. 5 (executive)
ALTER TABLE employees ADD COLUMN IF NOT EXISTS overtime BOOLEAN;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS business_travel VARCHAR(30);    -- Non Travel / Travel Rarely / Travel Frequently
ALTER TABLE employees ADD COLUMN IF NOT EXISTS distance_from_home INT;         -- km
ALTER TABLE employees ADD COLUMN IF NOT EXISTS education_level VARCHAR(30);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS education_field VARCHAR(100);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS total_working_years INT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS num_companies_worked INT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS years_in_current_role INT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS years_since_last_promotion INT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS years_with_curr_manager INT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS stock_option_level INT;         -- 0 .. 3
ALTER TABLE employees ADD COLUMN IF NOT EXISTS percent_salary_hike INT;        -- last raise, %
ALTER TABLE employees ADD COLUMN IF NOT EXISTS environment_satisfaction INT;   -- 1 .. 4
ALTER TABLE employees ADD COLUMN IF NOT EXISTS relationship_satisfaction INT;  -- 1 .. 4
ALTER TABLE employees ADD COLUMN IF NOT EXISTS training_times_last_year INT;

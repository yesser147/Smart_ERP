-- Requirement-by-requirement candidate scoring (AI engine, models/recruitment/matcher.py)

-- The job's requirements as the AI understood them (must-haves / nice-to-haves), cached
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS ai_requirements JSONB;

-- Per application: each requirement with met / partial / missing and the evidence from the CV
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS ai_match_details JSONB;

-- Scores computed with the previous method have no checklist: recompute them with the new one
UPDATE job_applications
SET ai_match_score = NULL, ai_match_reasoning = NULL
WHERE ai_match_score IS NOT NULL AND ai_match_details IS NULL;

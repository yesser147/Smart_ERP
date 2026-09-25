// AI engine models (match the FastAPI responses)

export interface CurvePoint {
  budget: number;
  performance: number;
}

export interface DepartmentBaseline {
  department_id: number;
  department_name: string;
  department_type: string | null;
  business_unit: string | null;
  division_description: string | null;
  current_budget: number;
  current_performance: number;
  slider_min: number;
  slider_max: number;
  curve: CurvePoint[];
  peak_budget: number;
  peak_performance: number;
}

export interface SimulationResult {
  department_id: number;
  department_name: string;
  current_budget: number;
  current_performance: number;
  simulated_budget: number;
  simulated_performance: number;
  performance_gain: number;
}

export interface CandidateMatch {
  applicant_id: number;
  name: string;
  education_level: string | null;
  years_of_experience: number | null;
  skills: string;
  match_score: number;
  embedding_score?: number | null;
  ai_reasoning?: string | null;
}

export interface JobMatchResult {
  job_id: number;
  job_title: string;
  candidates: CandidateMatch[];
  required_skills?: string;
  required_experience_years?: number | null;
  n_applicants: number;
  n_processed: number;
  unprocessed_applicant_ids: number[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface CvSearchResult {
  applicant_id: number;
  name: string;
  education_level: string | null;
  years_of_experience: number | null;
  skills: string[];
  experience_profile: string | null;
  applied_for: string | null;
  relevance: number;
}

export interface JobDescriptionResult {
  title: string;
  description: string;
  skills: string[];
}

export interface InterviewQuestion {
  question: string;
  purpose: string;
  type: 'gap' | 'strength' | 'behavioral' | string;
}

export interface InterviewQuestions {
  gaps: string[];
  questions: InterviewQuestion[];
}

export interface RiskDriver {
  feature: string;
  impact_pct: number;
}

export interface ModelQuality {
  level: 'acceptable' | 'low' | 'insufficient' | 'unknown';
  cv_auc: number | null;
  cv_pr_auc?: number | null;
  risk_threshold?: number | null;
  churn_rate?: number | null;
}

export interface EmployeeRisk {
  employee_id: number;
  risk_score: number;
  threshold: number;
  high_risk: boolean;
  rank: number;
  total_active: number;
  drivers: RiskDriver[];
  model_quality: ModelQuality;
}

export interface AtRiskEmployee {
  employee_id: number;
  name: string;
  title: string | null;
  department: string | null;
  team: string | null;
  risk_score: number;
  high_risk: boolean;
  drivers: RiskDriver[];
}

export interface SurvivalCurves {
  years: number[];
  series: { name: string; values: number[]; employees: number; median_years: number | null }[];
}

export interface ModelStatus {
  name: string;
  trained_at: string | null;
  metrics: Record<string, any> | null;
}

export interface ModelsStatus {
  retention: ModelStatus;
  budget: ModelStatus;
  training: boolean;
}

export interface PopularQuestion {
  question: string;
  asked: number;
}

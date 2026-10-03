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

/** One line of the screening checklist the AI builds for a job. */
export interface JobRequirement {
  requirement: string;
  type: 'must' | 'nice';
  category: string;
}

/** That line checked against one candidate's CV. */
export interface RequirementCheck extends JobRequirement {
  status: 'met' | 'partial' | 'missing';
  evidence: string;
}

/** A chart chosen by the AI for a query result (validated by the AI engine). */
export interface ChartSpec {
  type: 'bar' | 'horizontal-bar' | 'stacked-bar' | 'line' | 'pie' | 'donut' | 'scatter';
  title: string;
  x: string;
  y: string[];
  series: string | null;
  y_format: 'number' | 'money' | 'percent';
}

/** A chart pinned to the dashboard, with fresh rows. */
export interface SavedChart {
  id: number;
  title: string;
  question: string;
  chart: ChartSpec;
  rows: Record<string, unknown>[];
  error: string | null;
  created_at: string | null;
}

/** Events of the streamed HR chatbot answer (newline-delimited JSON). */
export type AssistantEvent =
  | { type: 'data'; question: string; sql_query: string; tabular_data: Record<string, unknown>[] }
  | { type: 'chart'; chart: ChartSpec }
  | { type: 'text'; text: string }
  | { type: 'done' }
  | { type: 'error'; message: string };

export interface CandidateMatch {
  applicant_id: number;
  name: string;
  education_level: string | null;
  years_of_experience: number | null;
  skills: string;
  match_score: number;
  embedding_score?: number | null;
  ai_reasoning?: string | null;
  /** the checklist (empty when the candidate was not reviewed by the AI) */
  requirements?: RequirementCheck[];
  reviewed?: boolean;
}

export interface JobMatchResult {
  job_id: number;
  job_title: string;
  candidates: CandidateMatch[];
  required_skills?: string;
  required_experience_years?: number | null;
  requirements?: JobRequirement[];
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
  /** true when the title already existed: its skills were kept */
  known_title: boolean;
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

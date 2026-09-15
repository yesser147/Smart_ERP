export interface CurvePoint {
  budget: number;
  performance: number;
}

export interface DepartmentBaseline {
  department_id: number;
  department_name: string;
  current_budget: number;
  current_performance: number;
  slider_min: number;
  slider_max: number;
  curve: CurvePoint[];
  peak_budget: number;
  peak_performance: number;
  sliderValue: number;

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

// NEW: recruitment matching
export interface CandidateMatch {
  applicant_id: number;
  name: string;
  education_level: string | null;
  years_of_experience: number | null;
  skills: string;
  match_score: number;
  embedding_score?: number;
  ai_reasoning?: string | null; // NEW
}

export interface JobMatchResult {
  job_id: number;
  job_title: string;
  candidates: CandidateMatch[];
}
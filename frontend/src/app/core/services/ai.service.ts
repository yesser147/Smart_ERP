import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
  skills: string; // JSON string, e.g. '["Java","SQL"]'
  match_score: number; // 0-100
}

export interface JobMatchResult {
  job_id: number;
  job_title: string;
  candidates: CandidateMatch[];
}

@Injectable({
  providedIn: 'root'
})
export class AiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:8000/api/ai'; // Match your FastAPI port

  askAssistant(question: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/chat`, { question });
  }

  getBudgetAdvice(): Observable<any> {
    return this.http.get(`${this.baseUrl}/budget-advisor`);
  }

  getRetentionStrategy(): Observable<any> {
    return this.http.get(`${this.baseUrl}/retention-macro`);
  }

  // --- What-if budget simulator ---

  getDepartmentBaselines(): Observable<DepartmentBaseline[]> {
    return this.http.get<DepartmentBaseline[]>(`${this.baseUrl}/budget-advisor/departments`);
  }

  simulateBudget(departmentId: number, newBudget: number): Observable<SimulationResult> {
    return this.http.post<SimulationResult>(`${this.baseUrl}/budget-advisor/simulate`, {
      department_id: departmentId,
      new_budget: newBudget
    });
  }

  // --- Recruitment candidate matching (NEW) ---

  matchCandidates(jobId: number, topK: number = 10): Observable<JobMatchResult> {
    return this.http.get<JobMatchResult>(`${this.baseUrl}/recruitment/match/${jobId}`, {
      params: { top_k: topK }
    });
  }
}
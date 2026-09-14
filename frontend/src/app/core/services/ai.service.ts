import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DepartmentBaseline, JobMatchResult, SimulationResult } from '../models/ai.model';



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



matchCandidates(jobId: number, topK: number = 10, recomputeAll: boolean = false): Observable<JobMatchResult> {
  return this.http.get<JobMatchResult>(`${this.baseUrl}/recruitment/match/${jobId}`, {
    params: { top_k: topK, recompute_all: recomputeAll }
  });
}
  processCv(applicantId: number): Observable<any> {
  return this.http.post<any>(`${this.baseUrl}/recruitment/process-cv/${applicantId}`, {});
}
}
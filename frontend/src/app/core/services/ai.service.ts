import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, shareReplay } from 'rxjs';
import { ChatMessage, DepartmentBaseline, JobMatchResult, SimulationResult } from '../models/ai.model';

@Injectable({
  providedIn: 'root'
})
export class AiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:8000/api/ai'; // Match your FastAPI port

  // Cached: Overview + Retention page share a single HTTP call
  private retention$?: Observable<any>;

  askAssistant(question: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/chat`, { question });
  }

  getBudgetAdvice(): Observable<any> {
    return this.http.get(`${this.baseUrl}/budget-advisor`);
  }

  getRetentionStrategy(): Observable<any> {
    if (!this.retention$) {
      // shareReplay resets on error, so the Retry button still triggers a fresh call
      this.retention$ = this.http
        .get(`${this.baseUrl}/retention-macro`)
        .pipe(shareReplay(1));
    }
    return this.retention$;
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

  // --- Recruitment ---

  matchCandidates(jobId: number, topK: number = 10, recomputeAll: boolean = false): Observable<JobMatchResult> {
    return this.http.get<JobMatchResult>(`${this.baseUrl}/recruitment/match/${jobId}`, {
      params: { top_k: topK, recompute_all: recomputeAll }
    });
  }

  processCv(applicantId: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/recruitment/process-cv/${applicantId}`, {});
  }

  streamApplicantChat(applicantId: number, jobId: number, message: string): Observable<string> {
    return new Observable<string>(subscriber => {
      const controller = new AbortController();
      (async () => {
        try {
          const res = await fetch(`${this.baseUrl}/recruitment/chat/${applicantId}/${jobId}/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
            signal: controller.signal
          });
          if (!res.ok || !res.body) {
            let detail = 'Request failed';
            try { detail = (await res.json()).detail ?? detail; } catch { /* keep default */ }
            throw new Error(detail);
          }
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            subscriber.next(decoder.decode(value, { stream: true }));
          }
          subscriber.complete();
        } catch (e) {
          if (!controller.signal.aborted) subscriber.error(e);
        }
      })();
      return () => controller.abort();
    });
  }

  getApplicantChatHistory(applicantId: number, jobId: number): Observable<{ messages: ChatMessage[] }> {
    return this.http.get<{ messages: ChatMessage[] }>(
      `${this.baseUrl}/recruitment/chat/${applicantId}/${jobId}/history`
    );
  }

  resetApplicantChat(applicantId: number, jobId: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/recruitment/chat/${applicantId}/${jobId}`);
  }
}
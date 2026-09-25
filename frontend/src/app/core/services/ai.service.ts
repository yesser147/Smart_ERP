import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, shareReplay, catchError, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TokenService } from './token.service';
import {
  AtRiskEmployee, ChatMessage, CvSearchResult, DepartmentBaseline, EmployeeRisk, InterviewQuestions,
  JobDescriptionResult, JobMatchResult, ModelsStatus, PopularQuestion, SimulationResult, SurvivalCurves
} from '../models/ai.model';

@Injectable({ providedIn: 'root' })
export class AiService {
  private http = inject(HttpClient);
  private tokenService = inject(TokenService);
  private baseUrl = environment.aiUrl;

  // shared between the Overview card and the Retention page
  private retention$?: Observable<any>;

  // --- HR chatbot
  /** conversationId keeps each chat window's memory separate on the server. */
  askAssistant(question: string, conversationId?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/chat`, { question, conversation_id: conversationId });
  }

  popularQuestions(): Observable<PopularQuestion[]> {
    return this.http.get<PopularQuestion[]>(`${this.baseUrl}/chat/popular`);
  }

  // --- budget advisor
  getBudgetAdvice(): Observable<any> {
    return this.http.get(`${this.baseUrl}/budget-advisor`);
  }

  getDepartmentBaselines(): Observable<DepartmentBaseline[]> {
    return this.http.get<DepartmentBaseline[]>(`${this.baseUrl}/budget-advisor/departments`);
  }

  simulateBudget(departmentId: number, newBudget: number): Observable<SimulationResult> {
    return this.http.post<SimulationResult>(`${this.baseUrl}/budget-advisor/simulate`, {
      department_id: departmentId,
      new_budget: newBudget
    });
  }

  // --- retention
  getRetentionStrategy(): Observable<any> {
    if (!this.retention$) {
      this.retention$ = this.http.get(`${this.baseUrl}/retention-macro`).pipe(
        shareReplay(1),
        catchError(err => { this.retention$ = undefined; return throwError(() => err); })
      );
    }
    return this.retention$;
  }

  /** ML-only high-risk count + model quality (no LLM call). */
  getRetentionRiskScores(): Observable<any> {
    return this.http.get(`${this.baseUrl}/retention-risk-scores`);
  }

  getEmployeeRisk(employeeId: number): Observable<EmployeeRisk> {
    return this.http.get<EmployeeRisk>(`${this.baseUrl}/retention/employee/${employeeId}`);
  }

  getAtRiskEmployees(limit = 15): Observable<AtRiskEmployee[]> {
    return this.http.get<AtRiskEmployee[]>(`${this.baseUrl}/retention/at-risk`, { params: { limit } });
  }

  getRetentionCurves(): Observable<SurvivalCurves> {
    return this.http.get<SurvivalCurves>(`${this.baseUrl}/retention/survival`);
  }

  // --- recruitment
  matchCandidates(jobId: number, topK = 10, recomputeAll = false): Observable<JobMatchResult> {
    return this.http.get<JobMatchResult>(`${this.baseUrl}/recruitment/match/${jobId}`, {
      params: { top_k: topK, recompute_all: recomputeAll }
    });
  }

  processCv(applicantId: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/recruitment/process-cv/${applicantId}`, {});
  }

  searchCvs(query: string, limit = 20): Observable<CvSearchResult[]> {
    return this.http.get<CvSearchResult[]>(`${this.baseUrl}/recruitment/search`, { params: { q: query, limit } });
  }

  generateJobDescription(title: string, department?: string, requiredExperienceYears?: number | null): Observable<JobDescriptionResult> {
    return this.http.post<JobDescriptionResult>(`${this.baseUrl}/recruitment/job-description`, {
      title, department, required_experience_years: requiredExperienceYears
    });
  }

  interviewQuestions(applicantId: number, jobId: number): Observable<InterviewQuestions> {
    return this.http.post<InterviewQuestions>(`${this.baseUrl}/recruitment/interview-questions/${applicantId}/${jobId}`, {});
  }

  streamApplicantChat(applicantId: number, jobId: number, message: string): Observable<string> {
    return new Observable<string>(subscriber => {
      const controller = new AbortController();
      (async () => {
        try {
          const res = await fetch(`${this.baseUrl}/recruitment/chat/${applicantId}/${jobId}/stream`, {
            method: 'POST',
            // fetch() bypasses the HttpClient interceptor, so add the token here
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${this.tokenService.getToken() ?? ''}`
            },
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
    return this.http.get<{ messages: ChatMessage[] }>(`${this.baseUrl}/recruitment/chat/${applicantId}/${jobId}/history`);
  }

  resetApplicantChat(applicantId: number, jobId: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/recruitment/chat/${applicantId}/${jobId}`);
  }

  // --- model monitoring (admin)
  modelsStatus(): Observable<ModelsStatus> {
    return this.http.get<ModelsStatus>(`${this.baseUrl}/models`);
  }

  retrainModels(): Observable<ModelsStatus> {
    return this.http.post<ModelsStatus>(`${this.baseUrl}/models/retrain`, {});
  }
}

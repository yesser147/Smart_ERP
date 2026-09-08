import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
}
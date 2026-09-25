import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  EmployeeDTO, EmployeeTrainingDTO, EngagementSurveyDTO, LeaveRequestDTO, LeaveType,
  PerformanceReviewDTO, SalaryHistoryDTO
} from '../models/hr.model';

/** Employee self-service: the logged-in user's own file. */
@Injectable({ providedIn: 'root' })
export class MeService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/me`;

  profile(): Observable<EmployeeDTO> { return this.http.get<EmployeeDTO>(`${this.apiUrl}/employee`); }
  salaryHistory(): Observable<SalaryHistoryDTO[]> { return this.http.get<SalaryHistoryDTO[]>(`${this.apiUrl}/salary-history`); }
  trainings(): Observable<EmployeeTrainingDTO[]> { return this.http.get<EmployeeTrainingDTO[]>(`${this.apiUrl}/trainings`); }
  surveys(): Observable<EngagementSurveyDTO[]> { return this.http.get<EngagementSurveyDTO[]>(`${this.apiUrl}/surveys`); }
  reviews(): Observable<PerformanceReviewDTO[]> { return this.http.get<PerformanceReviewDTO[]>(`${this.apiUrl}/reviews`); }
  leaveRequests(): Observable<LeaveRequestDTO[]> { return this.http.get<LeaveRequestDTO[]>(`${this.apiUrl}/leave-requests`); }

  requestLeave(body: { leaveType: LeaveType; startDate: string; endDate: string; reason?: string }): Observable<LeaveRequestDTO> {
    return this.http.post<LeaveRequestDTO>(`${this.apiUrl}/leave-requests`, body);
  }
}

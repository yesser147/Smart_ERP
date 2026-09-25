import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ApplicantDTO, ApplicantWithCvStatus, BudgetAllocationDTO, DepartmentDTO, EmployeeDTO,
  EmployeeTrainingDTO, EngagementSurveyDTO, JobApplicationDTO, JobPostingCreate, JobPostingDTO,
  LeaveRequestDTO, PageResponse, PerformanceReviewDTO, SalaryHistoryDTO, StatusHistoryDTO
} from '../models/hr.model';

export interface HireResult { employeeId: number; email: string; activationEmailSent: boolean; }

@Injectable({ providedIn: 'root' })
export class HrService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/hr`;

  // --- teams
  getAllDepartments(): Observable<DepartmentDTO[]> {
    return this.http.get<DepartmentDTO[]>(`${this.apiUrl}/departments`);
  }

  // --- employees
  getEmployeesPaged(page: number, size: number, search: string, sortBy: string, sortDir: string): Observable<PageResponse<EmployeeDTO>> {
    return this.http.get<PageResponse<EmployeeDTO>>(`${this.apiUrl}/employees/paged`, {
      params: { page, size, search: search || '', sortBy, sortDir }
    });
  }

  getEmployeeById(id: number): Observable<EmployeeDTO> {
    return this.http.get<EmployeeDTO>(`${this.apiUrl}/employees/${id}`);
  }

  getEmployeeSalaryHistory(id: number): Observable<SalaryHistoryDTO[]> {
    return this.http.get<SalaryHistoryDTO[]>(`${this.apiUrl}/employees/${id}/salary-history`);
  }

  getEmployeeTrainings(id: number): Observable<EmployeeTrainingDTO[]> {
    return this.http.get<EmployeeTrainingDTO[]>(`${this.apiUrl}/employees/${id}/trainings`);
  }

  getEmployeeSurveys(id: number): Observable<EngagementSurveyDTO[]> {
    return this.http.get<EngagementSurveyDTO[]>(`${this.apiUrl}/employees/${id}/surveys`);
  }

  getEmployeeReviews(id: number): Observable<PerformanceReviewDTO[]> {
    return this.http.get<PerformanceReviewDTO[]>(`${this.apiUrl}/employees/${id}/reviews`);
  }

  addEmployeeReview(id: number, rating: number, comments: string): Observable<PerformanceReviewDTO> {
    return this.http.post<PerformanceReviewDTO>(`${this.apiUrl}/employees/${id}/reviews`, { rating, comments });
  }

  exportPayroll(): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/payroll/export`, { responseType: 'blob' });
  }

  // --- job postings
  getAllJobPostings(): Observable<JobPostingDTO[]> {
    return this.http.get<JobPostingDTO[]>(`${this.apiUrl}/job-postings`);
  }

  getJobPosting(id: number): Observable<JobPostingDTO> {
    return this.http.get<JobPostingDTO>(`${this.apiUrl}/job-postings/${id}`);
  }

  createJobPosting(body: JobPostingCreate): Observable<JobPostingDTO> {
    return this.http.post<JobPostingDTO>(`${this.apiUrl}/job-postings`, body);
  }

  setJobPostingStatus(id: number, status: 'OPEN' | 'CLOSED' | 'FILLED'): Observable<JobPostingDTO> {
    return this.http.patch<JobPostingDTO>(`${this.apiUrl}/job-postings/${id}/status`, { status });
  }

  getApplicationsForJob(jobId: number): Observable<JobApplicationDTO[]> {
    return this.http.get<JobApplicationDTO[]>(`${this.apiUrl}/job-postings/${jobId}/applications`);
  }

  // --- applicants & applications
  getApplicantsWithCvStatus(): Observable<ApplicantWithCvStatus[]> {
    return this.http.get<ApplicantWithCvStatus[]>(`${this.apiUrl}/applicants-with-cv-status`);
  }

  getApplicantById(id: number): Observable<ApplicantDTO> {
    return this.http.get<ApplicantDTO>(`${this.apiUrl}/applicants/${id}`);
  }

  getApplicationsForApplicant(applicantId: number): Observable<JobApplicationDTO[]> {
    return this.http.get<JobApplicationDTO[]>(`${this.apiUrl}/applicants/${applicantId}/applications`);
  }

  getApplicationHistory(applicationId: string): Observable<StatusHistoryDTO[]> {
    return this.http.get<StatusHistoryDTO[]>(`${this.apiUrl}/job-applications/${applicationId}/history`);
  }

  moveToInterview(applicationId: string): Observable<JobApplicationDTO> {
    return this.http.patch<JobApplicationDTO>(`${this.apiUrl}/job-applications/${applicationId}/interview`, {});
  }

  moveToOffered(applicationId: string): Observable<JobApplicationDTO> {
    return this.http.patch<JobApplicationDTO>(`${this.apiUrl}/job-applications/${applicationId}/offer`, {});
  }

  rejectApplication(applicationId: string): Observable<JobApplicationDTO> {
    return this.http.patch<JobApplicationDTO>(`${this.apiUrl}/job-applications/${applicationId}/reject`, {});
  }

  hireApplicant(applicantId: number, payload: unknown): Observable<HireResult> {
    return this.http.post<HireResult>(`${this.apiUrl}/applicants/${applicantId}/hire`, payload);
  }

  // --- leave requests (HR side)
  getLeaveRequests(status?: string): Observable<LeaveRequestDTO[]> {
    return this.http.get<LeaveRequestDTO[]>(`${this.apiUrl}/leave-requests`, { params: status ? { status } : {} });
  }

  decideLeave(id: number, approve: boolean): Observable<LeaveRequestDTO> {
    return this.http.patch<LeaveRequestDTO>(`${this.apiUrl}/leave-requests/${id}/${approve ? 'approve' : 'reject'}`, {});
  }

  // --- budget allocations
  getBudgetAllocations(): Observable<BudgetAllocationDTO[]> {
    return this.http.get<BudgetAllocationDTO[]>(`${this.apiUrl}/budget-allocations`);
  }

  approveBudgetAllocation(body: { departmentId: number; allocatedBudget: number; predictedPerformance?: number | null; fiscalPeriod?: string }): Observable<BudgetAllocationDTO> {
    return this.http.post<BudgetAllocationDTO>(`${this.apiUrl}/budget-allocations`, body);
  }
}

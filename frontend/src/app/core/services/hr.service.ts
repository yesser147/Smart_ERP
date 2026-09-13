import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ApplicantCvDTO,
  ApplicantDTO,
  ApplicantWithCvStatus,
  DepartmentDTO,
  EmployeeDTO,
  EmployeeTrainingDTO,
  EngagementSurveyDTO,
  JobApplicationDTO,
  JobPostingDTO,
  SalaryHistoryDTO,
  TrainingCourseDTO
} from '../models/hr.model';

@Injectable({
  providedIn: 'root'
})
export class HrService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/hr`;

  // --- Employees ---
  getAllEmployees(): Observable<EmployeeDTO[]> {
    return this.http.get<EmployeeDTO[]>(`${this.apiUrl}/employees`);
  }

  // --- Departments ---
  getAllDepartments(): Observable<DepartmentDTO[]> {
    return this.http.get<DepartmentDTO[]>(`${this.apiUrl}/departments`);
  }

  getDepartmentById(id: number): Observable<DepartmentDTO> {
    return this.http.get<DepartmentDTO>(`${this.apiUrl}/departments/${id}`);
  }

  // --- Salary & Training ---
  getAllSalaryHistory(): Observable<SalaryHistoryDTO[]> {
    return this.http.get<SalaryHistoryDTO[]>(`${this.apiUrl}/salary-history`);
  }

  getAllTrainingCourses(): Observable<TrainingCourseDTO[]> {
    return this.http.get<TrainingCourseDTO[]>(`${this.apiUrl}/training-courses`);
  }

  getAllEmployeeTrainings(): Observable<EmployeeTrainingDTO[]> {
    return this.http.get<EmployeeTrainingDTO[]>(`${this.apiUrl}/employee-trainings`);
  }

  // --- Surveys ---
  getAllEngagementSurveys(): Observable<EngagementSurveyDTO[]> {
    return this.http.get<EngagementSurveyDTO[]>(`${this.apiUrl}/engagement-surveys`);
  }

  // --- Recruitment / ATS ---
  getAllApplicants(): Observable<ApplicantDTO[]> {
    return this.http.get<ApplicantDTO[]>(`${this.apiUrl}/applicants`);
  }

  getAllJobPostings(): Observable<JobPostingDTO[]> {
    return this.http.get<JobPostingDTO[]>(`${this.apiUrl}/job-postings`);
  }

  getAllJobApplications(): Observable<JobApplicationDTO[]> {
    return this.http.get<JobApplicationDTO[]>(`${this.apiUrl}/job-applications`);
  }

  getAllApplicantCvs(): Observable<ApplicantCvDTO[]> {
    return this.http.get<ApplicantCvDTO[]>(`${this.apiUrl}/applicant-cvs`);
  }

  // Add to your existing HrService class

moveToInterview(applicationId: string): Observable<JobApplicationDTO> {
  return this.http.patch<JobApplicationDTO>(`${this.apiUrl}/job-applications/${applicationId}/interview`, {});
}

moveToOffered(applicationId: string): Observable<JobApplicationDTO> {
  return this.http.patch<JobApplicationDTO>(`${this.apiUrl}/job-applications/${applicationId}/offer`, {});
}

rejectApplication(applicationId: string): Observable<JobApplicationDTO> {
  return this.http.patch<JobApplicationDTO>(`${this.apiUrl}/job-applications/${applicationId}/reject`, {});
}

getApplicantById(id: number): Observable<ApplicantDTO> {
  return this.http.get<ApplicantDTO>(`${this.apiUrl}/applicants/${id}`);
}

hireApplicant(applicantId: number, payload: any): Observable<{ employeeId: number; email: string }> {
  return this.http.post<{ employeeId: number; email: string }>(`${this.apiUrl}/applicants/${applicantId}/hire`, payload);
}

getEmployeeById(id: number): Observable<EmployeeDTO> {
  return this.http.get<EmployeeDTO>(`${this.apiUrl}/employees/${id}`);
}


getApplicantsWithCvStatus(): Observable<ApplicantWithCvStatus[]> {
  return this.http.get<ApplicantWithCvStatus[]>(`${this.apiUrl}/applicants-with-cv-status`);
}


}

export { ApplicantWithCvStatus };

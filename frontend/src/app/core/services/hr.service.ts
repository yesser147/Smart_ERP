import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ApplicantCvDTO,
  ApplicantDTO,
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
}
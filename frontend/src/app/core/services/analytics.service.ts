import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin, shareReplay, catchError, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  DepartmentSalarySummaryDTO, DepartmentSummaryDTO, DepartmentTypeTurnoverDTO,
  EmployeePerformanceEngagementDTO, GenderPayGapDTO, KpiSummaryDTO, RecruitmentFunnelAtsDTO,
  TimeToHireDTO, TopPerformerBenchmarksDTO, TrainingAnalyticsDTO
} from '../models/analytics.model';
import { JobPostingDTO } from '../models/hr.model';
import { HrService } from './hr.service';

export interface DashboardData {
  kpis: KpiSummaryDTO;
  turnoverType: DepartmentTypeTurnoverDTO[];
  salary: DepartmentSalarySummaryDTO[];
  funnel: RecruitmentFunnelAtsDTO[];
  training: TrainingAnalyticsDTO[];
  topPerformers: TopPerformerBenchmarksDTO[];
  performance: EmployeePerformanceEngagementDTO[];
  payGap: GenderPayGapDTO[];
  timeToHire: TimeToHireDTO[];
  jobPostings: JobPostingDTO[];
  departmentSummary: DepartmentSummaryDTO[];
}

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private http = inject(HttpClient);
  private hr = inject(HrService);
  private apiUrl = `${environment.apiUrl}/analytics`;

  /** Everything the analytics pages need, loaded once and shared between
   *  them (moving from Overview to Turnover doesn't reload anything). */
  private dashboard$?: Observable<DashboardData>;

  dashboard(): Observable<DashboardData> {
    if (!this.dashboard$) {
      this.dashboard$ = forkJoin({
        kpis: this.http.get<KpiSummaryDTO>(`${this.apiUrl}/kpis`),
        turnoverType: this.http.get<DepartmentTypeTurnoverDTO[]>(`${this.apiUrl}/typeturnover`),
        salary: this.http.get<DepartmentSalarySummaryDTO[]>(`${this.apiUrl}/salary-summary`),
        funnel: this.http.get<RecruitmentFunnelAtsDTO[]>(`${this.apiUrl}/recruitment-funnel`),
        training: this.http.get<TrainingAnalyticsDTO[]>(`${this.apiUrl}/training`),
        topPerformers: this.http.get<TopPerformerBenchmarksDTO[]>(`${this.apiUrl}/top-performers`),
        performance: this.http.get<EmployeePerformanceEngagementDTO[]>(`${this.apiUrl}/performance-engagement`),
        payGap: this.http.get<GenderPayGapDTO[]>(`${this.apiUrl}/pay-gap`),
        timeToHire: this.http.get<TimeToHireDTO[]>(`${this.apiUrl}/time-to-hire`),
        jobPostings: this.hr.getAllJobPostings(),
        departmentSummary: this.http.get<DepartmentSummaryDTO[]>(`${this.apiUrl}/department-summary`),
      }).pipe(
        shareReplay(1),
        catchError(err => { this.dashboard$ = undefined; return throwError(() => err); })
      );
    }
    return this.dashboard$;
  }

  /** Forget the cached data (after a change, or with the Refresh button). */
  invalidate(): void {
    this.dashboard$ = undefined;
  }
}

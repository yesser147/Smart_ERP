import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  AttritionRiskIndicatorsDTO, 
  DepartmentTurnoverDTO, 
  DepartmentTypeTurnoverDTO, 
  EmployeePerformanceEngagementDTO, 
  RecruitmentFunnelAtsDTO, 
  SalaryDistributionDTO, 
  TopPerformerBenchmarksDTO, 
  TrainingAnalyticsDTO 
} from '../models/analytics.model';

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/analytics`;

  getTurnoverStats(): Observable<DepartmentTurnoverDTO[]> {
    return this.http.get<DepartmentTurnoverDTO[]>(`${this.apiUrl}/turnover`);
  }
   getTurnoverTypeStats(): Observable<DepartmentTypeTurnoverDTO[]> {
    return this.http.get<DepartmentTypeTurnoverDTO[]>(`${this.apiUrl}/typeturnover`);
  }

  getRiskStats(): Observable<AttritionRiskIndicatorsDTO[]> {
    return this.http.get<AttritionRiskIndicatorsDTO[]>(`${this.apiUrl}/risk`);
  }

  getPerformanceEngagementStats(): Observable<EmployeePerformanceEngagementDTO[]> {
    return this.http.get<EmployeePerformanceEngagementDTO[]>(`${this.apiUrl}/performance-engagement`);
  }

  getSalaryDistributionStats(): Observable<SalaryDistributionDTO[]> {
    return this.http.get<SalaryDistributionDTO[]>(`${this.apiUrl}/salary-distribution`);
  }

  getRecruitmentFunnelStats(): Observable<RecruitmentFunnelAtsDTO[]> {
    return this.http.get<RecruitmentFunnelAtsDTO[]>(`${this.apiUrl}/recruitment-funnel`);
  }

  getTrainingAnalyticsStats(): Observable<TrainingAnalyticsDTO[]> {
    return this.http.get<TrainingAnalyticsDTO[]>(`${this.apiUrl}/training`);
  }

  getTopPerformerBenchmarksStats(): Observable<TopPerformerBenchmarksDTO[]> {
    return this.http.get<TopPerformerBenchmarksDTO[]>(`${this.apiUrl}/top-performers`);
  }
}
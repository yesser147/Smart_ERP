export interface AttritionRiskIndicatorsDTO {
  employeeId: number;
  departmentId: number;
  jobFunction: string;
  title: string;
  performanceScore: string;
  salary: number;
  startDate: string; 
  recentEngagement: number;
  recentSatisfaction: number;
  recentWlb: number;
  heuristicRiskLevel: string; // usually 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface DepartmentTurnoverDTO {
  departmentId: number;
  businessUnit: string;
  totalEmployees: number;
  activeCount: number;
  terminatedCount: number;
  turnoverRatePct: number;
}

export interface EmployeePerformanceEngagementDTO {
  employeeId: number;
  departmentId: number;
  jobFunction: string;
  title: string;
  performanceScore: string;
  avgEngagementScore: number;
  avgSatisfactionScore: number;
  avgWorkLifeBalance: number;
}

export interface RecruitmentFunnelAtsDTO {
  jobId: number;
  jobTitle: string;
  departmentId: number;
  postingStatus: string;
  offeredSalaryMin: number;
  offeredSalaryMax: number;
  totalApplications: number;
  pendingApplications: number;
  hiredCount: number;
  rejectedCount: number;
  avgDesiredSalary: number;
  avgAiMatchScore: number;
}

export interface SalaryDistributionDTO {
  departmentId: number;
  businessUnit: string;
  jobFunction: string;
  employeeCount: number;
  avgSalary: number;
  minSalary: number;
  maxSalary: number;
  totalPayrollBurden: number;
}

export interface TopPerformerBenchmarksDTO {
  employeeId: number;
  departmentId: number;
  jobFunction: string;
  title: string;
  performanceScore: string;
  gender: string;
  avgEngagement: number;
}

export interface TrainingAnalyticsDTO {
  departmentId: number;
  businessUnit: string;
  trainedEmployeesCount: number;
  totalTrainingsCompleted: number;
  totalTrainingInvestment: number;
  avgCourseDurationDays: number;
}

export interface DepartmentTypeTurnoverDTO{

    departmentType:string;
    totalEmployees:number;
    activeCount:number;
    terminatedCount:number;
    turnoverRatePct:number;

}
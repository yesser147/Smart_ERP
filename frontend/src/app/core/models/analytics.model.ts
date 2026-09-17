export interface KpiSummaryDTO {
  totalEmployees: number;
  activeEmployees: number;
  departmentCount: number;
  openJobPostings: number;
  avgEngagement: number;
  companyTurnoverRate: number;
  highRiskCount: number;
}
export interface DepartmentSummaryDTO {
  departmentId: number;
  businessUnit: string;
  departmentType: string;
  divisionDescription: string;
  headcount: number;
  totalEverEmployed: number; // NEW
  avgSalary: number | null;
  turnoverRatePct: number;
  activeCount: number;
  terminatedCount: number;
}

export interface DepartmentSalarySummaryDTO {
  businessUnit: string;
  divisionDescription: string;
  avgSalary: number;
}

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
  heuristicRiskLevel: string;
}

export interface DepartmentTurnoverDTO {
  departmentId?: number;
  businessUnit?: string;
  departmentType?: string;
  divisionDescription?: string;
  totalEmployees?: number;
  activeCount?: number;
  terminatedCount?: number; // FIXED: was "terminationsCount", didn't match backend JSON key
  turnoverRatePct?: number;
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
  appliedCount: number;
  inReviewCount: number;
  interviewingCount: number;
  offeredCount: number;
  rejectedCount: number;
  avgDesiredSalary: number;
  avgAiMatchScore: number;
}

export interface SalaryDistributionDTO {
  departmentId: number;
  businessUnit: string;
  divisionDescription: string;
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
  divisionDescription: string;
  trainedEmployeesCount: number;
  totalTrainingsCompleted: number;
  totalTrainingInvestment: number;
  avgCourseDurationDays: number;
}

export interface DepartmentTypeTurnoverDTO {
  departmentType: string;
  totalEmployees: number;
  activeCount: number;
  terminatedCount: number;
  turnoverRatePct: number;
}

export interface GenderPayGapDTO {
  departmentType: string;
  divisionDescription: string;
  gender: string;
  avgSalary: number;
  employeeCount: number;
}

export interface TimeToHireDTO {
  jobId: number;
  jobTitle: string;
  departmentId: number;
  avgDaysToHire: number;
  hiredCount: number;
}
// HR domain models (match the Spring backend DTOs)

export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  number: number; // current page index (0-based)
  size: number;
}

export interface DepartmentDTO {
  departmentId: number;
  businessUnit: string;
  departmentType: string;
  divisionDescription: string;
}

export interface EmployeeDTO {
  employeeId: number;
  departmentId: number;
  departmentName: string;
  managerId: number | null;
  managerName: string | null;
  firstName: string;
  lastName: string;
  startDate: string;
  exitDate: string | null;
  title: string;
  employeeStatus: string;
  employeeType: string;
  employeeClassificationType: string;
  terminationType: string | null;
  terminationDescription: string | null;
  dob: string | null;
  state: string | null;
  jobFunction: string;
  gender: string;
  location: string;
  performanceScore: string;
  currentEmployeeRating: number | null;
  salary: number;
  currency: string;
  needsReview: boolean;
  // detailed attributes (IBM HR data set); null for people hired in the app
  jobLevel?: number | null;
  overtime?: boolean | null;
  businessTravel?: string | null;
  distanceFromHome?: number | null;
  educationLevel?: string | null;
  educationField?: string | null;
  totalWorkingYears?: number | null;
  numCompaniesWorked?: number | null;
  yearsInCurrentRole?: number | null;
  yearsSinceLastPromotion?: number | null;
  yearsWithCurrManager?: number | null;
  stockOptionLevel?: number | null;
  percentSalaryHike?: number | null;
  trainingTimesLastYear?: number | null;
}

export interface SalaryHistoryDTO {
  id: number;
  employeeId: number;
  effectiveDate: string;
  salary: number;
  currency: string;
  changeReason: string;
}

export interface EmployeeTrainingDTO {
  id: number;
  employeeId: number;
  employeeName: string;
  courseId: number;
  programName: string;
  trainingDate: string;
  completionStatus: string;
  location: string;
}

export interface EngagementSurveyDTO {
  id: number;
  employeeId: number;
  surveyDate: string;
  engagementScore: number;
  satisfactionScore: number;
  workLifeBalanceScore: number;
}

export interface PerformanceReviewDTO {
  id: number;
  employeeId: number;
  reviewer: string | null;
  reviewDate: string;
  rating: number;
  comments: string | null;
}

export type LeaveType = 'ANNUAL' | 'SICK' | 'UNPAID' | 'OTHER';

export interface LeaveRequestDTO {
  id: number;
  employeeId: number;
  employeeName: string;
  leaveType: LeaveType;
  startDate: string;
  endDate: string;
  days: number;
  reason: string | null;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  decidedBy: string | null;
  decidedAt: string | null;
  createdAt: string;
}

export interface ApplicantDTO {
  applicantId: number;
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string | null;
  educationLevel: string | null;
  yearsOfExperience: number | null;
  gender: string | null;
  dob: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  zipCode: string | null;
  country: string | null;
}

export interface ApplicantWithCvStatus {
  applicantId: number;
  firstName: string;
  lastName: string;
  email: string;
  educationLevel: string | null;
  yearsOfExperience: number | null;
  hasCv: boolean;
  isProcessed: boolean;
  createdAt: string;
}

export interface JobPostingDTO {
  jobId: number;
  title: string;
  departmentId: number;
  departmentType: string;
  businessUnit: string;
  divisionDescription: string;
  location: string;
  requiredExperienceYears: number | null;
  offeredSalaryMin: number | null;
  offeredSalaryMax: number | null;
  status: 'OPEN' | 'CLOSED' | 'FILLED' | string;
  applicantCount: number;
  description: string | null;
  createdAt: string;
}

export interface JobPostingCreate {
  title: string;
  departmentId: number;
  location?: string | null;
  requiredExperienceYears?: number | null;
  offeredSalaryMin?: number | null;
  offeredSalaryMax?: number | null;
  description?: string | null;
}

export interface JobApplicationDTO {
  applicationId: string;
  applicantId: number;
  applicantName: string;
  jobId: number;
  jobTitle: string;
  applicationDate: string;
  desiredSalary: number | null;
  status: string;
  aiMatchScore: number | null;
}

export interface StatusHistoryDTO {
  oldStatus: string | null;
  newStatus: string;
  changedBy: string | null;
  changedAt: string;
}

export interface BudgetAllocationDTO {
  id: number;
  departmentId: number;
  departmentName: string;
  allocatedBudget: number;
  predictedPerformance: number | null;
  fiscalPeriod: string;
  createdAt: string;
}

export interface PublicJobDTO {
  jobId: number;
  title: string;
  department: string;
  location: string;
  requiredExperienceYears: number | null;
  salaryMin: number | null;
  salaryMax: number | null;
  description: string | null;
  postedAt: string;
}

export interface NotificationDTO {
  id: number;
  title: string;
  message: string | null;
  link: string | null;
  read: boolean;
  createdAt: string;
}

export interface AdminUserDTO {
  id: string;
  email: string;
  role: string;
  active: boolean;
  employeeId: number | null;
  createdAt: string;
}

export interface AuditLogDTO {
  id: number;
  actor: string;
  action: string;
  entityType: string | null;
  entityId: string | null;
  details: string | null;
  createdAt: string;
}

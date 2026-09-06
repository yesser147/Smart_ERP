// ==========================================
// HR DOMAIN MODELS
// ==========================================

export interface ApplicantCvDTO {
  id: string; // UUID
  applicantId: number;
  fileUrl: string;
  parsedText: string;
  extractedSkillsJson: string;
}

export interface ApplicantDTO {
  applicantId: number;
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  educationLevel: string;
  yearsOfExperience: number;
  gender: string;
  dob: string; // LocalDate
  address: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
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
  managerId: number;
  managerName: string;
  firstName: string;
  lastName: string;
  startDate: string; // LocalDate
  exitDate: string; // LocalDate
  title: string;
  employeeStatus: string;
  employeeType: string;
  employeeClassificationType: string;
  terminationType: string;
  terminationDescription: string;
  dob: string; // LocalDate
  state: string;
  jobFunction: string;
  gender: string;
  location: string;
  performanceScore: string;
  currentEmployeeRating: number;
  salary: number;
  currency: string;
  needsReview: boolean;
}

export interface EmployeeTrainingDTO {
  id: number;
  employeeId: number;
  employeeName: string;
  courseId: number;
  programName: string;
  trainingDate: string; // LocalDate
  completionStatus: string;
  location: string;
}

export interface EngagementSurveyDTO {
  id: number;
  employeeId: number;
  surveyDate: string; // LocalDate
  engagementScore: number;
  satisfactionScore: number;
  workLifeBalanceScore: number;
}

export interface JobApplicationDTO {
  applicationId: string; // UUID
  applicantId: number;
  applicantName: string;
  jobId: number;
  jobTitle: string;
  applicationDate: string; // LocalDate
  desiredSalary: number;
  status: string;
  aiMatchScore: number;
}
export interface JobPostingDTO {
  jobId?: number;
  title: string;
  departmentId?: number;
  departmentName?: string;
  location?: string;
  requiredExperienceYears?: number;
  offeredSalaryMin?: number;
  offeredSalaryMax?: number;
  status: 'OPEN' | 'CLOSED' | 'DRAFT' | string;
  applicantCount?: number;
}

export interface SalaryHistoryDTO {
  id: number;
  employeeId: number;
  effectiveDate: string; // LocalDate
  salary: number;
  currency: string;
  changeReason: string;
}

export interface TrainingCourseDTO {
  courseId: number;
  programName: string;
  trainingType: string;
  trainer: string;
  durationDays: number;
  cost: number;
  isActive: boolean;
}
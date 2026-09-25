export type RoleName = 'ROLE_ADMIN' | 'ROLE_HR_MANAGER' | 'ROLE_EMPLOYEE' | 'ROLE_MANAGER';

export const ROLE_LABELS: Record<string, string> = {
  ROLE_ADMIN: 'Administrator',
  ROLE_HR_MANAGER: 'HR Manager',
  ROLE_MANAGER: 'Manager',
  ROLE_EMPLOYEE: 'Employee',
};

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role: RoleName;
}

export interface AuthResponse {
  accessToken: string;
  userId: string;
  employeeId: number | null;
  email: string;
  role: RoleName;
}

export interface SetPasswordRequest {
  token: string;
  newPassword: string;
}

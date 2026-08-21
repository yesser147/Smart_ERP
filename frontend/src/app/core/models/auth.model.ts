export type RoleName = 'ROLE_ADMIN' | 'ROLE_HR_MANAGER' | 'ROLE_EMPLOYEE' | 'ROLE_MANAGER';

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
  tokenType: string;
  userId: string;
  email: string;
  role: RoleName;
  employeeId:Number,
}
export interface setpass{
  token: string;
  newPassword: string;


}
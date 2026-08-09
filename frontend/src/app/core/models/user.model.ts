import { RoleName } from './auth.model';

export interface BaseEntity {
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface User extends BaseEntity {
  id: string; // Matches UUID from Spring Boot
  email: string;
  firstName?: string;
  lastName?: string;
  role: RoleName;
}
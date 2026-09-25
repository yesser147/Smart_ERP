import { Injectable } from '@angular/core';
import { AuthResponse, RoleName } from '../models/auth.model';

export interface StoredUser {
  userId: string;
  employeeId: number | null;
  email: string;
  role: RoleName;
}

@Injectable({ providedIn: 'root' })
export class TokenService {
  private readonly TOKEN_KEY = 'smart_erp_access_token';
  private readonly USER_KEY = 'smart_erp_user_info';

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  saveAuthData(auth: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, auth.accessToken);
    const user: StoredUser = { userId: auth.userId, employeeId: auth.employeeId, email: auth.email, role: auth.role };
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  getUserInfo(): StoredUser | null {
    const json = localStorage.getItem(this.USER_KEY);
    try {
      return json ? JSON.parse(json) : null;
    } catch {
      return null;
    }
  }

  getUserRole(): RoleName | null {
    return this.getUserInfo()?.role ?? null;
  }

  hasAnyRole(roles: RoleName[]): boolean {
    const role = this.getUserRole();
    return !!role && roles.includes(role);
  }

  clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /** True only for a present, well-formed, not yet expired JWT. */
  isTokenValid(): boolean {
    const token = this.getToken();
    if (!token) return false;
    try {
      const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const payload = JSON.parse(atob(part));
      return typeof payload.exp === 'number' && payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }
}

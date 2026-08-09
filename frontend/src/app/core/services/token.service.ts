import { Injectable, signal } from '@angular/core';
import { AuthResponse, RoleName } from '../models/auth.model';

@Injectable({
  providedIn: 'root'
})
export class TokenService {
  private readonly TOKEN_KEY = 'smart_erp_access_token';
  private readonly USER_KEY = 'smart_erp_user_info';

  tokenSignal = signal<string | null>(this.getToken());
  userRoleSignal = signal<RoleName | null>(this.getUserRole());

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  saveAuthData(authResponse: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, authResponse.accessToken);
    localStorage.setItem(this.USER_KEY, JSON.stringify({
      userId: authResponse.userId,
      email: authResponse.email,
      role: authResponse.role
    }));

    this.tokenSignal.set(authResponse.accessToken);
    this.userRoleSignal.set(authResponse.role);
  }

  getUserRole(): RoleName | null {
    const user = this.getUserInfo();
    return user ? user.role : null;
  }

  getUserInfo(): { userId: string; email: string; role: RoleName } | null {
    const userJson = localStorage.getItem(this.USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
  }

  clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.tokenSignal.set(null);
    this.userRoleSignal.set(null);
  }

  hasToken(): boolean {
    return !!this.getToken();
  }

}
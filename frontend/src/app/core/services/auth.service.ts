import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { Router } from '@angular/router';
import { AuthResponse, LoginRequest, RegisterRequest, setpass } from '../models/auth.model';
import { TokenService } from './token.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private tokenService = inject(TokenService);
  private router = inject(Router);

  // Update port/host if different in your environment
  private apiUrl = 'http://localhost:8080/api/v1/auth';

  isAuthenticated = signal<boolean>(this.tokenService.hasToken());

  //tap:allows you to perform actions behind the scenes.
  //.pipe() allows you to chain RxJS operators together to process,transform, or inspect data flowing through the Observable before it reaches the subscriber

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      tap((response) => {
        if (response.accessToken) {
          this.tokenService.saveAuthData(response);
          this.isAuthenticated.set(true);
        }
      })
    );
  }


  createUser(userData: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/register`, userData);
  }

  setpassword(newpass: setpass): Observable<string> {
  return this.http.post(`${this.apiUrl}/set-password`, newpass, { responseType: 'text' });
}

  logout(): void {
    this.tokenService.clearAuthData();
    this.isAuthenticated.set(false);
    this.router.navigate(['/auth/login']);
  }
}
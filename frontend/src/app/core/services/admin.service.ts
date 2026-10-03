import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AdminUserDTO, AuditLogDTO, PageResponse } from '../models/hr.model';
import { AuthResponse, RoleName } from '../models/auth.model';

export interface EmployeeOption { employeeId: number; name: string; title: string | null; team: string | null; }

@Injectable({ providedIn: 'root' })
export class AdminService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/admin`;

  users(page: number, size: number, search: string, role: string): Observable<PageResponse<AdminUserDTO>> {
    return this.http.get<PageResponse<AdminUserDTO>>(`${this.apiUrl}/users`, {
      params: { page, size, search: search || '', ...(role ? { role } : {}) }
    });
  }

  /** Current employees who don't have a login yet. */
  employeesWithoutAccount(search: string): Observable<EmployeeOption[]> {
    return this.http.get<EmployeeOption[]>(`${this.apiUrl}/employees-without-account`, { params: { search } });
  }

  createAccount(body: { employeeId: number; email: string; password: string; role: RoleName }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/users`, body);
  }

  changeRole(id: string, role: string): Observable<AdminUserDTO> {
    return this.http.patch<AdminUserDTO>(`${this.apiUrl}/users/${id}/role`, { role });
  }

  setActive(id: string, active: boolean): Observable<AdminUserDTO> {
    return this.http.patch<AdminUserDTO>(`${this.apiUrl}/users/${id}/active`, { active });
  }

  audit(page: number, size: number, search: string): Observable<PageResponse<AuditLogDTO>> {
    return this.http.get<PageResponse<AuditLogDTO>>(`${this.apiUrl}/audit`, { params: { page, size, search: search || '' } });
  }
}

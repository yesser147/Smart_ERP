import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AdminUserDTO, AuditLogDTO, PageResponse } from '../models/hr.model';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/admin`;

  users(page: number, size: number, search: string, role: string): Observable<PageResponse<AdminUserDTO>> {
    return this.http.get<PageResponse<AdminUserDTO>>(`${this.apiUrl}/users`, {
      params: { page, size, search: search || '', ...(role ? { role } : {}) }
    });
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

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { PublicJobDTO } from '../models/hr.model';

/** Careers site: no login needed. */
@Injectable({ providedIn: 'root' })
export class PublicService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/public`;

  openJobs(): Observable<PublicJobDTO[]> {
    return this.http.get<PublicJobDTO[]>(`${this.apiUrl}/jobs`);
  }

  apply(form: FormData): Observable<{ applicantId: number; applicationId: string; message: string }> {
    return this.http.post<{ applicantId: number; applicationId: string; message: string }>(`${this.apiUrl}/applications`, form);
  }
}

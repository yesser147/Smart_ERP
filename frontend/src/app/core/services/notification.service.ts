import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subscription, timer, switchMap, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { NotificationDTO } from '../models/hr.model';

/** In-app notifications, refreshed every minute while the shell is open. */
@Injectable({ providedIn: 'root' })
export class NotificationService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/notifications`;
  private polling?: Subscription;

  readonly items = signal<NotificationDTO[]>([]);
  readonly unread = signal(0);

  start(): void {
    if (this.polling) return;
    this.polling = timer(0, 60_000).pipe(
      switchMap(() => this.http.get<{ unread: number; items: NotificationDTO[] }>(this.apiUrl)
        .pipe(catchError(() => of(null))))
    ).subscribe(res => {
      if (!res) return;
      this.items.set(res.items);
      this.unread.set(res.unread);
    });
  }

  stop(): void {
    this.polling?.unsubscribe();
    this.polling = undefined;
    this.items.set([]);
    this.unread.set(0);
  }

  markRead(n: NotificationDTO): void {
    if (n.read) return;
    this.http.post<void>(`${this.apiUrl}/${n.id}/read`, {}).subscribe(() => {
      this.items.update(list => list.map(x => x.id === n.id ? { ...x, read: true } : x));
      this.unread.update(u => Math.max(0, u - 1));
    });
  }

  markAllRead(): void {
    this.http.post<void>(`${this.apiUrl}/read-all`, {}).subscribe(() => {
      this.items.update(list => list.map(x => ({ ...x, read: true })));
      this.unread.set(0);
    });
  }
}

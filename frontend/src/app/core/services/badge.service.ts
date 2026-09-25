import { Injectable, inject, signal } from '@angular/core';
import { HrService } from './hr.service';

/** Counters shown as badges in the sidebar. */
@Injectable({ providedIn: 'root' })
export class BadgeService {
  private hr = inject(HrService);

  readonly pendingLeave = signal(0);

  refreshPendingLeave(): void {
    this.hr.getLeaveRequests('PENDING').subscribe({
      next: list => this.pendingLeave.set(list.length),
      error: () => this.pendingLeave.set(0)
    });
  }
}

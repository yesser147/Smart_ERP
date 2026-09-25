import { Component, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { HrService } from '../../../core/services/hr.service';
import { BadgeService } from '../../../core/services/badge.service';
import { LeaveRequestDTO } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

type Filter = 'PENDING' | 'APPROVED' | 'REJECTED' | '';
const PAGE_SIZE = 20;

export const LEAVE_LABELS: Record<string, string> = {
  ANNUAL: 'Annual leave', SICK: 'Sick leave', UNPAID: 'Unpaid leave', OTHER: 'Other',
};

@Component({
  selector: 'app-leave-approvals',
  standalone: true,
  imports: [DatePipe, FormsModule, RouterLink, PageHeaderComponent, StatusBadgeComponent, IconComponent],
  templateUrl: './leave-approvals.component.html'
})
export class LeaveApprovalsComponent implements OnInit {
  private hr = inject(HrService);
  private badges = inject(BadgeService);

  requests: LeaveRequestDTO[] = [];
  loading = true;
  error = false;
  filter: Filter = 'PENDING';
  search = '';
  page = 1;
  busy = new Set<number>();
  actionError: string | null = null;
  readonly labels = LEAVE_LABELS;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = false;
    // every pending request + the most recent history (the API caps the history at 200)
    forkJoin({ pending: this.hr.getLeaveRequests('PENDING'), recent: this.hr.getLeaveRequests() }).subscribe({
      next: ({ pending, recent }) => {
        const byId = new Map([...recent, ...pending].map(r => [r.id, r]));
        this.requests = [...byId.values()];
        this.loading = false;
      },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  count(f: Filter): number {
    return f ? this.requests.filter(r => r.status === f).length : this.requests.length;
  }

  get filtered(): LeaveRequestDTO[] {
    const q = this.search.trim().toLowerCase();
    return this.requests
      .filter(r => !this.filter || r.status === this.filter)
      .filter(r => !q || r.employeeName.toLowerCase().includes(q))
      // pending: the soonest first; history: the most recent first
      .sort((a, b) => this.filter === 'PENDING'
        ? a.startDate.localeCompare(b.startDate)
        : b.startDate.localeCompare(a.startDate));
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filtered.length / PAGE_SIZE));
  }

  get pageRows(): LeaveRequestDTO[] {
    return this.filtered.slice((this.page - 1) * PAGE_SIZE, this.page * PAGE_SIZE);
  }

  setFilter(f: Filter): void {
    this.filter = f;
    this.page = 1;
  }

  goTo(p: number): void {
    this.page = Math.min(Math.max(1, p), this.totalPages);
  }

  resetPage(): void {
    this.page = 1;
  }

  decide(r: LeaveRequestDTO, approve: boolean): void {
    this.busy.add(r.id);
    this.actionError = null;
    this.hr.decideLeave(r.id, approve).subscribe({
      next: updated => {
        this.requests = this.requests.map(x => (x.id === updated.id ? updated : x));
        this.busy.delete(r.id);
        this.badges.refreshPendingLeave();
      },
      error: err => {
        this.actionError = errorMessage(err, 'The request could not be updated.');
        this.busy.delete(r.id);
      }
    });
  }
}

import { Component, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { MeService } from '../../core/services/me.service';
import { TokenService } from '../../core/services/token.service';
import {
  EmployeeDTO, EmployeeTrainingDTO, EngagementSurveyDTO, LeaveRequestDTO, LeaveType,
  PerformanceReviewDTO, SalaryHistoryDTO
} from '../../core/models/hr.model';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { IconComponent } from '../../shared/components/icon/icon.component';
import { errorMessage } from '../../shared/utils/errors';
import { EmployeeFileComponent } from '../people/employee-file/employee-file.component';
import { LEAVE_LABELS } from '../people/leave-approvals/leave-approvals.component';

/** Self-service: the signed-in employee's own file and leave requests. */
@Component({
  selector: 'app-my-space',
  standalone: true,
  imports: [DatePipe, FormsModule, PageHeaderComponent, StatusBadgeComponent, IconComponent, EmployeeFileComponent],
  templateUrl: './my-space.component.html'
})
export class MySpaceComponent implements OnInit {
  private me = inject(MeService);
  private tokenService = inject(TokenService);

  readonly linked = !!this.tokenService.getUserInfo()?.employeeId;
  readonly labels = LEAVE_LABELS;
  readonly leaveTypes = Object.keys(LEAVE_LABELS) as LeaveType[];
  readonly today = new Date().toISOString().slice(0, 10);

  employee: EmployeeDTO | null = null;
  salaryHistory: SalaryHistoryDTO[] = [];
  trainings: EmployeeTrainingDTO[] = [];
  surveys: EngagementSurveyDTO[] = [];
  reviews: PerformanceReviewDTO[] = [];
  leave: LeaveRequestDTO[] = [];
  loading = true;
  error = false;

  // leave form
  showLeaveForm = false;
  leaveType: LeaveType = 'ANNUAL';
  startDate = '';
  endDate = '';
  reason = '';
  sending = false;
  leaveError: string | null = null;

  ngOnInit(): void {
    if (!this.linked) {
      this.loading = false;
      return;
    }
    forkJoin({
      employee: this.me.profile(),
      salary: this.me.salaryHistory(),
      trainings: this.me.trainings(),
      surveys: this.me.surveys(),
      reviews: this.me.reviews(),
      leave: this.me.leaveRequests(),
    }).subscribe({
      next: d => {
        this.employee = d.employee;
        this.salaryHistory = d.salary;
        this.trainings = d.trainings;
        this.surveys = d.surveys;
        this.reviews = d.reviews;
        this.leave = d.leave;
        this.loading = false;
      },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  /** Same rule as the backend: only current employees ask for leave. */
  get canRequestLeave(): boolean {
    const s = (this.employee?.employeeStatus ?? '').toLowerCase();
    return s === 'active' || s === 'on leave';
  }

  /** Approved days in the current calendar year. */
  get daysTakenThisYear(): number {
    const year = new Date().getFullYear().toString();
    return this.leave.filter(l => l.status === 'APPROVED' && l.startDate.startsWith(year))
      .reduce((s, l) => s + l.days, 0);
  }

  get pendingCount(): number {
    return this.leave.filter(l => l.status === 'PENDING').length;
  }

  get requestedDays(): number {
    if (!this.startDate || !this.endDate || this.endDate < this.startDate) return 0;
    return Math.round((new Date(this.endDate).getTime() - new Date(this.startDate).getTime()) / 86_400_000) + 1;
  }

  requestLeave(): void {
    if (!this.startDate || !this.endDate || this.endDate < this.startDate) {
      this.leaveError = 'Choose a start date and an end date after it.';
      return;
    }
    this.sending = true;
    this.leaveError = null;
    this.me.requestLeave({ leaveType: this.leaveType, startDate: this.startDate, endDate: this.endDate, reason: this.reason.trim() || undefined })
      .subscribe({
        next: created => {
          this.leave = [created, ...this.leave];
          this.sending = false;
          this.showLeaveForm = false;
          this.startDate = this.endDate = this.reason = '';
        },
        error: err => {
          this.leaveError = errorMessage(err, 'The request could not be sent.');
          this.sending = false;
        }
      });
  }
}

import { Component, Input } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass } from '@angular/common';
import {
  EmployeeDTO, EmployeeTrainingDTO, EngagementSurveyDTO, PerformanceReviewDTO, SalaryHistoryDTO
} from '../../../core/models/hr.model';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

type Tab = 'profile' | 'pay' | 'performance' | 'training';

/**
 * An employee's file, shared by the HR page (employee-detail) and the
 * self-service page (my-space). Page-specific cards are projected:
 *   <div aside>…</div>        right column
 *   <div review-form>…</div>  top of the Performance tab
 */
@Component({
  selector: 'app-employee-file',
  standalone: true,
  imports: [DatePipe, DecimalPipe, NgClass, StatusBadgeComponent, IconComponent],
  templateUrl: './employee-file.component.html'
})
export class EmployeeFileComponent {
  @Input({ required: true }) employee!: EmployeeDTO;
  @Input() salaryHistory: SalaryHistoryDTO[] = [];
  @Input() trainings: EmployeeTrainingDTO[] = [];
  @Input() surveys: EngagementSurveyDTO[] = [];
  @Input() reviews: PerformanceReviewDTO[] = [];

  tab: Tab = 'profile';

  readonly tabs: { key: Tab; label: string }[] = [
    { key: 'profile', label: 'Profile' },
    { key: 'pay', label: 'Compensation' },
    { key: 'performance', label: 'Performance' },
    { key: 'training', label: 'Training' },
  ];

  get left(): boolean {
    return (this.employee.employeeStatus ?? '').toLowerCase().includes('terminat');
  }

  get tenureYears(): number | null {
    const e = this.employee;
    if (!e.startDate) return null;
    const end = e.exitDate ? new Date(e.exitDate).getTime() : Date.now();
    return Math.round(((end - new Date(e.startDate).getTime()) / (365.25 * 24 * 3600 * 1000)) * 10) / 10;
  }

  private avg(pick: (s: EngagementSurveyDTO) => number): number | null {
    if (!this.surveys.length) return null;
    return this.surveys.reduce((sum, s) => sum + (pick(s) ?? 0), 0) / this.surveys.length;
  }

  get engagement() { return this.avg(s => s.engagementScore); }
  get satisfaction() { return this.avg(s => s.satisfactionScore); }
  get workLife() { return this.avg(s => s.workLifeBalanceScore); }

  /** Salary change vs the previous entry (history is newest first). */
  change(i: number): number | null {
    const prev = this.salaryHistory[i + 1];
    if (!prev || !prev.salary) return null;
    return ((this.salaryHistory[i].salary - prev.salary) / prev.salary) * 100;
  }

  stars(rating: number): number[] {
    return [1, 2, 3, 4, 5].map(i => (i <= rating ? 1 : 0));
  }

  performanceTone(score: string | null | undefined): string {
    const s = (score ?? '').toUpperCase();
    if (s.includes('EXCEED')) return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
    if (s.includes('FULLY') || s.includes('MEET')) return 'bg-sky-500/10 text-sky-300 border-sky-500/20';
    if (s.includes('NEEDS') || s.includes('PIP') || s.includes('BELOW')) return 'bg-amber-500/10 text-amber-300 border-amber-500/20';
    return 'bg-slate-500/10 text-slate-300 border-slate-500/20';
  }
}

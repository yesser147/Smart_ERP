import { Component, Input } from '@angular/core';
import { NgClass } from '@angular/common';

const STYLES: Record<string, string> = {
  OPEN: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  ACTIVE: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  APPROVED: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  OFFERED: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  FILLED: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
  APPLIED: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
  'IN REVIEW': 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  PENDING: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  INTERVIEWING: 'bg-sky-500/10 text-sky-300 border-sky-500/20',
  CLOSED: 'bg-slate-500/10 text-slate-300 border-slate-500/20',
  INACTIVE: 'bg-slate-500/10 text-slate-300 border-slate-500/20',
  REJECTED: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  TERMINATED: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
};

/** Coloured pill for any workflow status (job, application, leave, employee). */
@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [NgClass],
  template: `<span class="erp-badge" [ngClass]="style">{{ label || status }}</span>`
})
export class StatusBadgeComponent {
  @Input() status: string | null | undefined = '';
  @Input() label = '';

  get style(): string {
    const key = (this.status ?? '').toUpperCase();
    if (STYLES[key]) return STYLES[key];
    if (key.includes('TERMINATED') || key.includes('VOLUNTARILY')) return STYLES['TERMINATED'];
    return 'bg-slate-500/10 text-slate-300 border-slate-500/20';
  }
}

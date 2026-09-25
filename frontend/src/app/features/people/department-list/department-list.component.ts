import { Component, OnInit, inject } from '@angular/core';
import { DecimalPipe, NgClass } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { DepartmentSummaryDTO } from '../../../core/models/analytics.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

export interface DepartmentRow {
  departmentType: string;
  teams: number;
  headcount: number;
  avgSalary: number | null;
  turnoverPct: number;
}

export function turnoverTone(pct: number): string {
  if (pct >= 20) return 'bg-rose-500/10 text-rose-300 border-rose-500/20';
  if (pct >= 10) return 'bg-amber-500/10 text-amber-300 border-amber-500/20';
  return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
}

/** One card per department (department_type), built from the per-team summary. */
@Component({
  selector: 'app-department-list',
  standalone: true,
  imports: [DecimalPipe, NgClass, RouterLink, PageHeaderComponent, IconComponent],
  templateUrl: './department-list.component.html'
})
export class DepartmentListComponent implements OnInit {
  private analytics = inject(AnalyticsService);

  rows: DepartmentRow[] = [];
  loading = true;
  error = false;
  readonly turnoverTone = turnoverTone;

  ngOnInit(): void {
    this.analytics.dashboard().subscribe({
      next: d => { this.rows = this.group(d.departmentSummary); this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  get totalHeadcount(): number {
    return this.rows.reduce((s, r) => s + r.headcount, 0);
  }

  /** Salary and turnover are weighted by headcount so a tiny team doesn't skew them. */
  private group(teams: DepartmentSummaryDTO[]): DepartmentRow[] {
    const byType = new Map<string, DepartmentSummaryDTO[]>();
    teams.forEach(t => {
      const key = t.departmentType || 'Unclassified';
      byType.set(key, [...(byType.get(key) ?? []), t]);
    });
    return [...byType.entries()].map(([departmentType, list]) => {
      const headcount = list.reduce((s, t) => s + (t.headcount || 0), 0);
      const everEmployed = list.reduce((s, t) => s + (t.totalEverEmployed || 0), 0);
      const left = list.reduce((s, t) => s + (t.terminatedCount || 0), 0);
      const salary = list.reduce((s, t) => s + (t.avgSalary || 0) * (t.headcount || 0), 0);
      return {
        departmentType,
        teams: list.length,
        headcount,
        avgSalary: headcount ? salary / headcount : null,
        turnoverPct: everEmployed ? (left / everEmployed) * 100 : 0,
      };
    }).sort((a, b) => b.headcount - a.headcount);
  }
}

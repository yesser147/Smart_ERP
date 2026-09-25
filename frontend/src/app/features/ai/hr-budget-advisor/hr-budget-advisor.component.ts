import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, debounceTime, switchMap, catchError, of } from 'rxjs';
import { NgApexchartsModule } from 'ng-apexcharts';

import { AiService } from '../../../core/services/ai.service';
import { HrService } from '../../../core/services/hr.service';
import { BudgetAllocationDTO } from '../../../core/models/hr.model';
import { DepartmentBaseline, SimulationResult } from '../../../core/models/ai.model';
import { DARK_CHART, GRID } from '../../../shared/utils/chart-theme';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { errorMessage } from '../../../shared/utils/errors';

@Component({
  selector: 'app-hr-budget-advisor',
  standalone: true,
  imports: [DatePipe, DecimalPipe, NgClass, FormsModule, NgApexchartsModule, PageHeaderComponent, IconComponent, MarkdownPipe],
  templateUrl: './hr-budget-advisor.component.html'
})
export class HrBudgetAdvisorComponent implements OnInit {
  private ai = inject(AiService);
  private hr = inject(HrService);
  private destroyRef = inject(DestroyRef);

  loading = true;
  error: string | null = null;
  data: any = null;
  showQualityDetails = false;

  teams: DepartmentBaseline[] = [];
  typeFilter = '';
  selectedId: number | null = null;
  curveChart: any = null;

  // what-if
  budget = 0;
  simulation: SimulationResult | null = null;
  simulating = false;
  private simulate$ = new Subject<void>();

  // approval
  fiscalPeriod = `${new Date().getFullYear()}`;
  approving = false;
  approveMessage: string | null = null;
  approveError: string | null = null;
  allocations: BudgetAllocationDTO[] = [];

  ngOnInit(): void {
    this.simulate$.pipe(
      debounceTime(250),
      switchMap(() => {
        this.simulating = true;
        return this.ai.simulateBudget(this.selectedId!, this.budget).pipe(catchError(() => of(null)));
      }),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(res => {
      this.simulation = res;
      this.simulating = false;
    });

    this.load();
    this.loadAllocations();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.ai.getBudgetAdvice().subscribe({
      next: res => {
        this.data = res;
        this.ai.getDepartmentBaselines().subscribe({
          next: teams => {
            this.teams = teams;
            this.select(res.recommended_allocations?.[0]?.department_id ?? teams[0]?.department_id ?? null);
            this.loading = false;
          },
          error: err => { this.error = errorMessage(err, 'The AI engine is not reachable.'); this.loading = false; }
        });
      },
      error: err => { this.error = errorMessage(err, 'The AI engine is not reachable.'); this.loading = false; }
    });
  }

  private loadAllocations(): void {
    this.hr.getBudgetAllocations().subscribe(list => this.allocations = list);
  }

  get types(): string[] {
    return [...new Set(this.teams.map(t => t.department_type).filter((t): t is string => !!t))].sort();
  }

  get filteredTeams(): DepartmentBaseline[] {
    return this.teams.filter(t => !this.typeFilter || t.department_type === this.typeFilter);
  }

  get team(): DepartmentBaseline | undefined {
    return this.teams.find(t => t.department_id === this.selectedId);
  }

  get quality(): string {
    return this.data?.model_quality?.level ?? 'unknown';
  }

  onTypeChange(): void {
    if (!this.filteredTeams.some(t => t.department_id === this.selectedId)) {
      this.select(this.filteredTeams[0]?.department_id ?? null);
    }
  }

  select(id: number | null): void {
    this.selectedId = id;
    this.approveMessage = this.approveError = null;
    const t = this.team;
    if (!t) return;
    this.budget = Math.round(t.peak_budget);
    this.simulation = null;
    this.simulate$.next();
    this.buildCurve(t);
  }

  onBudget(value: number): void {
    this.budget = Number(value);
    this.simulate$.next();
  }

  private buildCurve(t: DepartmentBaseline): void {
    this.curveChart = {
      series: [{ name: 'Predicted performance', data: t.curve.map(p => [Math.round(p.budget), Number(p.performance.toFixed(3))]) }],
      chart: { type: 'area', height: 280, ...DARK_CHART, zoom: { enabled: false } },
      colors: ['#38bdf8'],
      stroke: { curve: 'smooth', width: 2.5 },
      fill: { type: 'gradient', gradient: { shadeIntensity: 0.4, opacityFrom: 0.35, opacityTo: 0.02 } },
      dataLabels: { enabled: false },
      xaxis: {
        type: 'numeric',
        labels: { formatter: (v: number) => `$${Math.round(v / 1000)}k` },
        title: { text: 'Training budget', style: { color: '#64748b', fontWeight: 500 } },
      },
      yaxis: { labels: { formatter: (v: number) => v.toFixed(2) } },
      grid: GRID,
      tooltip: { theme: 'dark', x: { formatter: (v: number) => `Budget $${Math.round(v).toLocaleString('en-US')}` } },
      annotations: {
        xaxis: [
          { x: t.current_budget, borderColor: '#94a3b8', strokeDashArray: 4,
            label: { text: 'Current', style: { background: '#334155', color: '#fff' } } },
          { x: t.peak_budget, borderColor: '#f59e0b',
            label: { text: 'Predicted optimum', style: { background: '#f59e0b', color: '#000' } } },
        ]
      },
    };
  }

  approve(): void {
    const t = this.team;
    if (!t) return;
    if (!confirm(`Approve a training budget of $${this.budget.toLocaleString('en-US')} for ${t.department_name} (${this.fiscalPeriod})?`)) return;
    this.approving = true;
    this.approveMessage = this.approveError = null;
    this.hr.approveBudgetAllocation({
      departmentId: t.department_id,
      allocatedBudget: this.budget,
      predictedPerformance: this.simulation?.simulated_performance ?? null,
      fiscalPeriod: this.fiscalPeriod,
    }).subscribe({
      next: a => {
        this.allocations = [a, ...this.allocations];
        this.approving = false;
        this.approveMessage = 'Allocation approved and recorded.';
      },
      error: err => {
        this.approving = false;
        this.approveError = errorMessage(err, 'The allocation could not be saved.');
      }
    });
  }
}

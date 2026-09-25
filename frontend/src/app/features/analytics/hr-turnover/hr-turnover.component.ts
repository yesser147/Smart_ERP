import { Component, Input, OnChanges, OnInit, inject } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { NgApexchartsModule } from 'ng-apexcharts';
import { DepartmentSummaryDTO } from '../../../core/models/analytics.model';
import { AiService } from '../../../core/services/ai.service';
import { DARK_CHART, GRID, PALETTE } from '../../../shared/utils/chart-theme';
import { IconComponent } from '../../../shared/components/icon/icon.component';

/** Units with fewer people than this are hidden by default: one departure in a
 *  two-person team is a true but misleading 50% turnover. */
const MIN_HEADCOUNT = 3;
const PAGE_SIZE = 15;

@Component({
  selector: 'app-hr-turnover',
  standalone: true,
  imports: [DecimalPipe, FormsModule, RouterLink, NgApexchartsModule, IconComponent],
  templateUrl: './hr-turnover.component.html'
})
export class HrTurnoverComponent implements OnInit, OnChanges {
  private ai = inject(AiService);

  @Input() turnoverTypeChart: any;
  @Input() departmentSummary: DepartmentSummaryDTO[] = [];

  turnoverChart: any = null;
  survivalChart: any = null;
  survivalMedians: { name: string; median: number | null; employees: number }[] = [];
  survivalState: 'loading' | 'ready' | 'error' = 'loading';

  searchTerm = '';
  typeFilter = '';
  showTiny = false;
  page = 1;

  ngOnInit(): void {
    this.ai.getRetentionCurves().subscribe({
      next: curves => {
        const series = curves.series.map(s => ({ name: s.name, data: s.values }));
        this.survivalMedians = curves.series.map(s => ({ name: s.name, median: s.median_years, employees: s.employees }));
        this.survivalChart = {
          series,
          chart: { type: 'line', height: 340, ...DARK_CHART, zoom: { enabled: false } },
          xaxis: { categories: curves.years, title: { text: 'Years since hiring', style: { color: '#64748b', fontWeight: 500 } } },
          yaxis: { min: 0, max: 100, labels: { formatter: (v: number) => `${Math.round(v)}%` } },
          stroke: { width: series.map((_, i) => (i === 0 ? 4 : 2)), curve: 'stepline' },
          colors: ['#ffffff', ...PALETTE],
          grid: GRID,
          legend: { position: 'top', labels: { colors: '#94a3b8' } },
          tooltip: { theme: 'dark', y: { formatter: (v: number) => `${v}% still employed` } },
          dataLabels: { enabled: false },
        };
        this.survivalState = 'ready';
      },
      error: () => this.survivalState = 'error'
    });
  }

  ngOnChanges(): void {
    this.page = 1;
    this.buildDepartmentChart();
  }

  get types(): string[] {
    return [...new Set(this.departmentSummary.map(d => d.departmentType || 'Unclassified'))].sort();
  }

  private headcount(d: DepartmentSummaryDTO): number {
    return (d.activeCount ?? 0) + (d.terminatedCount ?? 0);
  }

  get filtered(): DepartmentSummaryDTO[] {
    const term = this.searchTerm.trim().toLowerCase();
    return this.departmentSummary
      .filter(d => this.showTiny || this.headcount(d) >= MIN_HEADCOUNT)
      .filter(d => !this.typeFilter || (d.departmentType || 'Unclassified') === this.typeFilter)
      .filter(d => !term || `${d.divisionDescription} ${d.businessUnit}`.toLowerCase().includes(term))
      .sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0));
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filtered.length / PAGE_SIZE));
  }

  get pageRows(): DepartmentSummaryDTO[] {
    return this.filtered.slice((this.page - 1) * PAGE_SIZE, this.page * PAGE_SIZE);
  }

  resetPage(): void {
    this.page = 1;
  }

  goTo(p: number): void {
    this.page = Math.min(Math.max(1, p), this.totalPages);
  }

  /** Top 10 teams by turnover, with a minimum size, still active. */
  private buildDepartmentChart(): void {
    const top = this.departmentSummary
      .filter(d => this.headcount(d) >= MIN_HEADCOUNT && (d.activeCount ?? 0) > 0)
      .sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0))
      .slice(0, 10);
    if (!top.length) {
      this.turnoverChart = null;
      return;
    }
    this.turnoverChart = {
      series: [{ name: 'Turnover %', data: top.map(d => d.turnoverRatePct ?? 0) }],
      chart: { type: 'bar', height: Math.max(320, top.length * 34), ...DARK_CHART },
      xaxis: { categories: top.map(d => `${d.divisionDescription || d.departmentType || 'Unknown'} (${d.businessUnit})`) },
      plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '65%', distributed: true } },
      dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}%` },
      colors: PALETTE,
      grid: GRID,
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `${v.toFixed(1)}%` } },
      legend: { show: false },
    };
  }
}

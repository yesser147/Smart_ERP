import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgApexchartsModule } from 'ng-apexcharts';
import { DepartmentSummaryDTO } from '../../../core/models/analytics.model';

const DARK_THEME_BASE = {
  foreColor: '#94a3b8',
  toolbar: { show: false },
  background: 'transparent',
};

// Departments with fewer than this many active+terminated people are
// excluded from the "highest turnover" chart AND from the table by
// default -- a single-person department that left shows as a
// mathematically true but misleading 100% turnover rate, drowning out
// real, representative departments. Both the chart and the table filter
// use the SAME field pair (activeCount + terminatedCount) so they never
// disagree on which departments count as "meaningful."
const MIN_HEADCOUNT = 3;

@Component({
  selector: 'app-hr-turnover',
  standalone: true,
  imports: [CommonModule, FormsModule, NgApexchartsModule],
  templateUrl: './hr-turnover.component.html'
})
export class HrTurnoverComponent implements OnChanges {
  @Input() turnoverTypeChart: any;
  @Input() departmentSummary: DepartmentSummaryDTO[] = [];

  turnoverChart: any;

  searchTerm = '';
  typeFilter = '';
  pageSize = 25;
  currentPage = 1;
  showTinyDepartments = false;

  ngOnChanges(): void {
    this.currentPage = 1;
    this.buildDepartmentChart();
  }

  get availableTypes(): string[] {
    const types = new Set(this.departmentSummary.map(d => d.departmentType || 'Unclassified'));
    return Array.from(types).sort();
  }

  private headcount(d: DepartmentSummaryDTO): number {
    return (d.activeCount ?? 0) + (d.terminatedCount ?? 0);
  }

  get filteredData(): DepartmentSummaryDTO[] {
    let result = [...this.departmentSummary];

    if (!this.showTinyDepartments) {
      result = result.filter(d => this.headcount(d) >= MIN_HEADCOUNT);
    }

    if (this.typeFilter) {
      result = result.filter(d => (d.departmentType || 'Unclassified') === this.typeFilter);
    }

    const term = this.searchTerm.trim().toLowerCase();
    if (term) {
      result = result.filter(d => (d.businessUnit || '').toLowerCase().includes(term));
    }

    return result.sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0));
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filteredData.length / this.pageSize));
  }

  get paginatedData(): DepartmentSummaryDTO[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filteredData.slice(start, start + this.pageSize);
  }

  onFilterChange(): void {
    this.currentPage = 1;
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) this.currentPage = page;
  }

  nextPage(): void { this.goToPage(this.currentPage + 1); }
  prevPage(): void { this.goToPage(this.currentPage - 1); }

  /** Builds the "highest turnover" bar chart from real, complete
   * departmentSummary data -- filtered to a minimum headcount so a
   * single departed employee in a tiny department can't produce a
   * misleading 100% bar, then takes the genuine top 10. Chart height
   * scales with the number of bars so nothing gets clipped. */
private buildDepartmentChart(): void {
  const meaningful = this.departmentSummary
    .filter(d => this.headcount(d) >= MIN_HEADCOUNT && (d.activeCount ?? 0) > 0) // exclude fully closed depts
    .sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0))
    .slice(0, 10);

  if (meaningful.length === 0) {
    this.turnoverChart = null;
    return;
  }

  const chartHeight = Math.max(340, meaningful.length * 40);

  this.turnoverChart = {
    series: [{ name: 'Turnover %', data: meaningful.map(d => d.turnoverRatePct ?? 0) }],
    chart: { type: 'bar', height: chartHeight, ...DARK_THEME_BASE },
    xaxis: {
      // meaningful label: division/type, not the raw site code
      categories: meaningful.map(d =>
        `${d.divisionDescription || d.departmentType || 'Unknown'} (${d.businessUnit})`
      )
    },
    plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true } },
    dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}%` },
    colors: ['#2dd4bf', '#22d3ee', '#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#fb923c', '#facc15', '#4ade80', '#f87171'],
    fill: { opacity: 0.9 },
    grid: { borderColor: '#334155', strokeDashArray: 4 },
    tooltip: { theme: 'dark', y: { formatter: (v: number) => `${v.toFixed(1)}%` } },
    legend: { show: false },
  };
}
}
import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  NgApexchartsModule, ApexAxisChartSeries, ApexChart, ApexXAxis,
  ApexPlotOptions, ApexDataLabels, ApexGrid, ApexTooltip, ApexLegend,
  ApexStroke, ApexMarkers
} from 'ng-apexcharts';
import { AiService } from '../../../core/services/ai.service';
import { DepartmentBaseline } from '../../../core/models/ai.model';

type BaseChartOptions = {
  series: ApexAxisChartSeries;
  chart: ApexChart;
  colors: string[];
  dataLabels: ApexDataLabels;
  tooltip: ApexTooltip;
  legend: ApexLegend;
  xaxis: ApexXAxis;
  grid: ApexGrid;
};

export type ComparisonChartOptions = BaseChartOptions & {
  plotOptions: ApexPlotOptions;
};

export type CurveChartOptions = BaseChartOptions & {
  stroke: ApexStroke;
  markers: ApexMarkers;
};

type FilterKey = 'division' | 'type' | 'unit';

const DARK_THEME_BASE: Partial<ApexChart> = {
  foreColor: '#94a3b8',
  toolbar: { show: false },
  background: 'transparent',
};

@Component({
  selector: 'app-hr-budget-advisor',
  standalone: true,
  imports: [CommonModule, FormsModule, NgApexchartsModule],
  templateUrl: './hr-budget-advisor.component.html'
})
export class HrBudgetAdvisorComponent implements OnInit {
  private aiService = inject(AiService);

  loading = true;
  error = false;
  data: any = null;
  showQualityDetails = false;

  departments: DepartmentBaseline[] = [];
  selectedDeptId: number | null = null;

  divisionFilter = '';
  typeFilter = '';
  unitFilter = '';

  comparisonChart!: ComparisonChartOptions;
  performanceCurveChart!: CurveChartOptions;

  ngOnInit(): void {
    this.fetchBudgetAdvice();
  }

  fetchBudgetAdvice(): void {
    this.loading = true;
    this.error = false;

    this.aiService.getBudgetAdvice().subscribe({
      next: (res) => {
        this.data = res;
        this.aiService.getDepartmentBaselines().subscribe({
          next: (baselines) => {
            this.departments = baselines;
            const firstRecommended = res.recommended_allocations?.[0]?.department_id;
            this.selectedDeptId = firstRecommended ?? baselines[0]?.department_id ?? null;
            this.onDeptChange();
            this.loading = false;
          },
          error: () => { this.error = true; this.loading = false; }
        });
      },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  private matches(d: DepartmentBaseline, skip?: FilterKey): boolean {
    if (skip !== 'division' && this.divisionFilter && d.division_description !== this.divisionFilter) return false;
    if (skip !== 'type' && this.typeFilter && d.department_type !== this.typeFilter) return false;
    if (skip !== 'unit' && this.unitFilter && d.business_unit !== this.unitFilter) return false;
    return true;
  }

  private uniqueSorted(values: (string | null | undefined)[]): string[] {
    return Array.from(new Set(values.filter((v): v is string => !!v))).sort();
  }

  get availableDivisions(): string[] {
    return this.uniqueSorted(
      this.departments.filter(d => this.matches(d, 'division')).map(d => d.division_description)
    );
  }

  get availableTypes(): string[] {
    return this.uniqueSorted(
      this.departments.filter(d => this.matches(d, 'type')).map(d => d.department_type)
    );
  }

  get availableUnits(): string[] {
    return this.uniqueSorted(
      this.departments.filter(d => this.matches(d, 'unit')).map(d => d.business_unit)
    );
  }

  get filteredDepartments(): DepartmentBaseline[] {
    return this.departments.filter(d => this.matches(d));
  }

  get hasActiveFilters(): boolean {
    return !!(this.divisionFilter || this.typeFilter || this.unitFilter);
  }

  onFilterChange(): void {
    if (this.divisionFilter && !this.availableDivisions.includes(this.divisionFilter)) this.divisionFilter = '';
    if (this.typeFilter && !this.availableTypes.includes(this.typeFilter)) this.typeFilter = '';
    if (this.unitFilter && !this.availableUnits.includes(this.unitFilter)) this.unitFilter = '';

    if (!this.filteredDepartments.some(d => d.department_id === this.selectedDeptId)) {
      this.selectedDeptId = this.filteredDepartments[0]?.department_id ?? null;
    }
    this.onDeptChange();
  }

  resetFilters(): void {
    this.divisionFilter = '';
    this.typeFilter = '';
    this.unitFilter = '';
    this.onFilterChange();
  }

  onDeptChange(): void {
    const dept = this.departments.find(d => d.department_id === this.selectedDeptId);
    if (!dept) return;

    const optimalBudget = dept.peak_budget;

    this.comparisonChart = {
      series: [{ name: 'Budget', data: [dept.current_budget, optimalBudget] }],
      chart: { type: 'bar', height: 240, ...DARK_THEME_BASE },
      colors: ['#64748b', '#2dd4bf'],
      plotOptions: { bar: { horizontal: false, columnWidth: '40%', borderRadius: 4, distributed: true } },
      dataLabels: { enabled: true, formatter: (v: number) => `$${v.toLocaleString()}` },
      xaxis: { categories: ['Current budget', 'AI-optimal budget'] },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { show: false },
    };

    const peakIndex = dept.curve.reduce((closestIdx, point, idx) =>
      Math.abs(point.budget - dept.peak_budget) < Math.abs(dept.curve[closestIdx].budget - dept.peak_budget)
        ? idx : closestIdx, 0);

    this.performanceCurveChart = {
      series: [{ name: 'Predicted performance', data: dept.curve.map(p => p.performance) }],
      chart: { type: 'line', height: 260, ...DARK_THEME_BASE },
      colors: ['#2dd4bf'],
      stroke: { curve: 'smooth', width: 3 },
      markers: {
        size: 0,
        strokeColors: '#fff',
        strokeWidth: 2,
        hover: { size: 7, sizeOffset: 0 },
        discrete: [{
          seriesIndex: 0,
          dataPointIndex: peakIndex,
          fillColor: '#f59e0b',
          strokeColor: '#fff',
          size: 7,
        }],
      },
      dataLabels: { enabled: false },
      xaxis: {
        categories: dept.curve.map(p => `$${(p.budget / 1000).toFixed(1)}k`),
        title: { text: 'Training budget', style: { color: '#64748b' } },
        crosshairs: { show: true },
        tooltip: { enabled: false },
      },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: {
        theme: 'dark',
        shared: false,
        intersect: false,
        x: {
          formatter: (_v: any, opts: any) => {
            const p = dept.curve[opts.dataPointIndex];
            return `Budget: $${Math.round(p.budget).toLocaleString()}`;
          },
        },
        y: {
          title: { formatter: () => 'Performance:' },
          formatter: (v: number) => v.toFixed(3) + ' pts',
        },
      },
      legend: { show: false },
      annotations: {
        points: [{
          x: `$${(dept.curve[peakIndex].budget / 1000).toFixed(1)}k`,
          y: dept.peak_performance,
          marker: { size: 0 },
          label: {
            text: `Optimal: $${Math.round(dept.peak_budget).toLocaleString()}`,
            style: { background: '#f59e0b', color: '#000', fontSize: '11px', fontWeight: 600 },
            offsetY: -10,
          }
        }]
      }
    } as any;
  }

  get selectedDept(): DepartmentBaseline | undefined {
    return this.departments.find(d => d.department_id === this.selectedDeptId);
  }

  get selectedRecommendation(): any {
    return this.data?.recommended_allocations?.find((a: any) => a.department_id === this.selectedDeptId);
  }

  /** Converts the LLM's lightweight markdown (**bold**, *italic*, "- " bullets,
   *  blank-line paragraphs) into safe HTML for [innerHTML]. Angular's default
   *  sanitizer allows strong/em/ul/li/p, so no DomSanitizer bypass is needed.
   *  Kept in sync with the identical method in the other AI components. */
  formatMemo(text: string | undefined | null): string {
    if (!text) return '';

    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    html = html
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>');

    const lines = html.split('\n');
    const out: string[] = [];
    let inList = false;

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (line.startsWith('- ')) {
        if (!inList) { out.push('<ul class="list-disc pl-5 space-y-1">'); inList = true; }
        out.push(`<li>${line.slice(2)}</li>`);
      } else {
        if (inList) { out.push('</ul>'); inList = false; }
        if (line) out.push(`<p class="mt-2 first:mt-0">${line}</p>`);
      }
    }
    if (inList) out.push('</ul>');

    return out.join('');
  }
}
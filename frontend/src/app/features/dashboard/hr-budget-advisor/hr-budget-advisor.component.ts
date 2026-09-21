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

  departments: DepartmentBaseline[] = [];
  selectedDeptId: number | null = null;

  // Independent filters ('' = all)
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

  // ---------- Cascading filters ----------

  // Does a department match all active filters, optionally ignoring one?
  private matches(d: DepartmentBaseline, skip?: FilterKey): boolean {
    if (skip !== 'division' && this.divisionFilter && d.division_description !== this.divisionFilter) return false;
    if (skip !== 'type' && this.typeFilter && d.department_type !== this.typeFilter) return false;
    if (skip !== 'unit' && this.unitFilter && d.business_unit !== this.unitFilter) return false;
    return true;
  }

  private uniqueSorted(values: (string | null | undefined)[]): string[] {
    return Array.from(new Set(values.filter((v): v is string => !!v))).sort();
  }

  // Each list is built from the departments matching the OTHER two filters,
  // so the current selection never hides its own alternatives.
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
    // Drop any selection that is no longer available after the change
    if (this.divisionFilter && !this.availableDivisions.includes(this.divisionFilter)) this.divisionFilter = '';
    if (this.typeFilter && !this.availableTypes.includes(this.typeFilter)) this.typeFilter = '';
    if (this.unitFilter && !this.availableUnits.includes(this.unitFilter)) this.unitFilter = '';

    // Keep the selected department valid
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

  // ---------- Charts ----------

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
      xaxis: { categories: ['Budget actuel', 'Budget optimal (IA)'] },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { show: false },
    };

    const peakIndex = dept.curve.reduce((closestIdx, point, idx) =>
      Math.abs(point.budget - dept.peak_budget) < Math.abs(dept.curve[closestIdx].budget - dept.peak_budget)
        ? idx : closestIdx, 0);

this.performanceCurveChart = {
  series: [{ name: 'Performance prédite', data: dept.curve.map(p => p.performance) }],
  chart: { type: 'line', height: 260, ...DARK_THEME_BASE },
  colors: ['#2dd4bf'],
  stroke: { curve: 'smooth', width: 3 },
  markers: {
    size: 0,
    strokeColors: '#fff',
    strokeWidth: 2,
    // Point shown under the cursor
    hover: { size: 7, sizeOffset: 0 },
    // Permanent marker on the optimal point
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
    title: { text: 'Budget de formation', style: { color: '#64748b' } },
    crosshairs: { show: true },
    tooltip: { enabled: false },
  },
  grid: { borderColor: '#334155', strokeDashArray: 4 },
  tooltip: {
    theme: 'dark',
    shared: false,
    intersect: false,
    x: {
      // Exact budget of the hovered point (not the rounded axis label)
      formatter: (_v: any, opts: any) => {
        const p = dept.curve[opts.dataPointIndex];
        return `Budget : $${Math.round(p.budget).toLocaleString()}`;
      },
    },
    y: {
      title: { formatter: () => 'Performance :' },
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
}
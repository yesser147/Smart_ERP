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

  // Full department list, used to power a single dropdown -- replaces
  // rendering every department's slider/curve at once.
  departments: DepartmentBaseline[] = [];
  selectedDeptId: number | null = null;

  comparisonChart!: ComparisonChartOptions;
  performanceCurveChart!: CurveChartOptions;

  ngOnInit(): void {
    this.fetchBudgetAdvice();
  }

  fetchBudgetAdvice(): void {
    this.loading = true;
    this.error = false;

    // Both calls already existed elsewhere in the app (memo + baselines) --
    // reusing them here instead of adding a new endpoint.
    this.aiService.getBudgetAdvice().subscribe({
      next: (res) => {
        this.data = res;
        this.aiService.getDepartmentBaselines().subscribe({
          next: (baselines) => {
            this.departments = baselines;
            // Default to the first recommended allocation's department if
            // one exists, else the first department overall.
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

  onDeptChange(): void {
    const dept = this.departments.find(d => d.department_id === this.selectedDeptId);
    if (!dept) return;

    const optimalBudget = dept.peak_budget;

    this.comparisonChart = {
      series: [{
        name: 'Budget',
        data: [dept.current_budget, optimalBudget]
      }],
      chart: { type: 'bar', height: 240, ...DARK_THEME_BASE },
      // `distributed: true` assigns one color per bar, so two colors for two bars
      colors: ['#64748b', '#2dd4bf'],
      plotOptions: { bar: { horizontal: false, columnWidth: '40%', borderRadius: 4, distributed: true } },
      dataLabels: { enabled: true, formatter: (v: number) => `$${v.toLocaleString()}` },
      xaxis: { categories: ['Budget actuel', 'Budget optimal (IA)'] },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { show: false },
    };

    this.performanceCurveChart = {
      series: [{ name: 'Performance prédite', data: dept.curve.map(p => p.performance) }],
      chart: { type: 'line', height: 260, ...DARK_THEME_BASE },
      colors: ['#2dd4bf'],
      stroke: { curve: 'smooth', width: 3 },
      markers: { size: 0 },
      dataLabels: { enabled: false },
      xaxis: {
        categories: dept.curve.map(p => `$${Math.round(p.budget / 1000)}k`),
        title: { text: 'Budget de formation', style: { color: '#64748b' } }
      },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => v.toFixed(3) + ' pts' } },
      legend: { show: false },
    };
  }

  get selectedDept(): DepartmentBaseline | undefined {
    return this.departments.find(d => d.department_id === this.selectedDeptId);
  }

  get selectedRecommendation(): any {
    return this.data?.recommended_allocations?.find((a: any) => a.department_id === this.selectedDeptId);
  }
}
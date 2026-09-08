import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  NgApexchartsModule,
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexPlotOptions,
  ApexDataLabels,
  ApexGrid,
  ApexTooltip,
  ApexLegend,
  ApexStroke,
  ApexMarkers,
  ApexFill
} from 'ng-apexcharts';
import { AiService } from '../../../core/services/ai.service';

export type ChartOptions = {
  series: ApexAxisChartSeries;
  chart: ApexChart;
  colors: string[];
  dataLabels: ApexDataLabels;
  tooltip: ApexTooltip;
  legend: ApexLegend;
  xaxis: ApexXAxis;
  plotOptions: ApexPlotOptions;
  grid: ApexGrid;
  stroke: ApexStroke;
  markers: ApexMarkers;
  fill: ApexFill;
};

const DARK_THEME_BASE: Partial<ApexChart> = {
  foreColor: '#94a3b8',
  toolbar: { show: false },
  background: 'transparent',
};

@Component({
  selector: 'app-hr-budget-advisor',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule],
  templateUrl: './hr-budget-advisor.component.html'
})
export class HrBudgetAdvisorComponent implements OnInit {
  private aiService = inject(AiService);

  loading = true;
  error = false;
  data: any = null;
  budgetChart!: ChartOptions;
  priceVariationChart!: ChartOptions;
  worstDeptsInfo: any[] = [];

  ngOnInit(): void {
    this.fetchBudgetAdvice();
  }

  fetchBudgetAdvice(): void {
    this.loading = true;
    this.error = false;

    this.aiService.getBudgetAdvice().subscribe({
      next: (res) => {
        this.data = res;
        this.budgetChart = this.buildBudgetComparisonChart(res.recommended_allocations || []);
        
        // Handles array of 3 worst departments (with fallback to single department payload)
        const worstDepts = res.chart_data?.worst_departments_price_tests || 
                          (res.chart_data?.worst_department_price_tests ? [res.chart_data.worst_department_price_tests] : []);

        if (worstDepts && worstDepts.length > 0) {
          this.worstDeptsInfo = worstDepts;
          this.priceVariationChart = this.buildPriceVariationChart(worstDepts);
        }
        
        this.loading = false;
      },
      error: () => {
        this.error = true;
        this.loading = false;
      }
    });
  }

  private buildBudgetComparisonChart(allocations: any[]): ChartOptions {
    const categories = allocations.map(a => a.department_name || `Dept ${a.department_id}`);
    const originalBudgets = allocations.map(a => a.current_budget ?? a.base_budget ?? 100000);
    const newBudgets = allocations.map((a, i) => originalBudgets[i] + (a.recommended_budget_increase || 0));

    return {
      series: [
        { name: 'Budget Actuel', data: originalBudgets },
        { name: 'Nouveau Budget Optimisé', data: newBudgets }
      ],
      chart: { type: 'bar', height: 300, ...DARK_THEME_BASE },
      colors: ['#64748b', '#2dd4bf'],
      plotOptions: { bar: { horizontal: false, columnWidth: '50%', borderRadius: 4 } },
      dataLabels: { enabled: false },
      xaxis: { categories },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { position: 'top', labels: { colors: '#94a3b8' } },
      stroke: { show: false },
      fill: { opacity: 1 },
      markers: { size: 0 }
    };
  }

  private buildPriceVariationChart(worstDeptsData: any[]): ChartOptions {
    // Extract price step categories (X-axis) from the first department
    const firstDeptTests = worstDeptsData[0]?.price_variations_tested || [];
    const categories = firstDeptTests.map((t: any) => `+$${t.added_budget.toLocaleString()}`);

    // Map each of the 3 worst departments to its own series
    const multiSeries = worstDeptsData.map((dept: any) => ({
      name: dept.department_name || `Dept #${dept.department_id}`,
      data: (dept.price_variations_tested || []).map((t: any) => t.performance_gain)
    }));

    return {
      series: multiSeries,
      chart: { type: 'area', height: 280, ...DARK_THEME_BASE },
      colors: ['#f59e0b', '#ec4899', '#3b82f6'], // Amber, Pink, Blue for the 3 departments
      stroke: { curve: 'smooth', width: 3 },
      fill: {
        type: 'gradient',
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.35,
          opacityTo: 0.05,
          stops: [0, 90, 100]
        }
      },
      markers: { size: 4, strokeWidth: 2 },
      plotOptions: { bar: { horizontal: false } },
      dataLabels: { enabled: false },
      xaxis: { 
        categories, 
        title: { text: 'Variations d\'Investissement Supplémentaires', style: { color: '#64748b' } } 
      },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `+${v.toFixed(3)} pts` } },
      legend: { show: true, position: 'top', labels: { colors: '#94a3b8' } }
    };
  }
}
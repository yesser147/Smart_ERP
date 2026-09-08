import { Component, Input, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';
import {
  NgApexchartsModule, ApexAxisChartSeries, ApexChart, ApexXAxis, ApexYAxis,
  ApexPlotOptions, ApexDataLabels, ApexFill, ApexGrid, ApexTooltip, ApexLegend,
  ApexNonAxisChartSeries, ApexResponsive, ApexMarkers, ApexStroke
} from 'ng-apexcharts';

import { AnalyticsService } from '../../../core/services/analytics.service';
import { HrService } from '../../../core/services/hr.service';
import { EmployeeDTO, JobPostingDTO } from '../../../core/models/hr.model';
import {
  KpiSummaryDTO,
  TopPerformerBenchmarksDTO,
  DepartmentTurnoverDTO,
  DepartmentSalarySummaryDTO,
  RecruitmentFunnelAtsDTO,
  TrainingAnalyticsDTO,
  EmployeePerformanceEngagementDTO,
  DepartmentTypeTurnoverDTO
} from '../../../core/models/analytics.model';

import { HrOverviewComponent } from '../hr-overview/hr-overview.component';
import { HrTurnoverComponent } from '../hr-turnover/hr-turnover.component';
import { HrCompensationComponent } from '../hr-compensation/hr-compensation.component';
import { HrRecruitmentComponent } from '../hr-recruitment/hr-recruitment.component';
import { HrRetentionComponent } from '../hr-retention/hr-retention.component';
import { HrBudgetAdvisorComponent } from '../hr-budget-advisor/hr-budget-advisor.component';

export type ChartOptions = {
  series: ApexAxisChartSeries | ApexNonAxisChartSeries;
  chart: ApexChart;
  colors: string[];
  dataLabels: ApexDataLabels;
  tooltip: ApexTooltip;
  legend: ApexLegend;
  xaxis?: ApexXAxis;
  yaxis?: ApexYAxis;
  labels?: string[];
  plotOptions?: ApexPlotOptions;
  fill?: ApexFill;
  grid?: ApexGrid;
  responsive?: ApexResponsive[];
  markers?: ApexMarkers;
  stroke?: ApexStroke;
};

const DARK_THEME_BASE: Partial<ApexChart> = {
  foreColor: '#94a3b8', 
  toolbar: { show: false },
  background: 'transparent',
};

@Component({
  selector: 'app-hr-dashboard',
  standalone: true,
  imports: [
    CommonModule, 
    NgApexchartsModule,
    HrOverviewComponent,
    HrTurnoverComponent,
    HrCompensationComponent,
    HrRecruitmentComponent,
    HrBudgetAdvisorComponent,
    HrRetentionComponent
  ],
  templateUrl: './hr-dashboard.component.html'
})
export class HrDashboardComponent implements OnInit {
  private analyticsService = inject(AnalyticsService);
  private hrService = inject(HrService);

  @Input() currentView: string = 'overview';
  
  loading = true;

  kpi!: KpiSummaryDTO;
  employees: EmployeeDTO[] = [];
  jobPostings: JobPostingDTO[] = [];
  topPerformers: TopPerformerBenchmarksDTO[] = [];
  turnoverData: DepartmentTurnoverDTO[] = [];

  turnoverChart!: ChartOptions;
  turnoverTypeChart!: ChartOptions;
  statusDonut!: ChartOptions;
  salaryChart!: ChartOptions;
  funnelChart!: ChartOptions;
  trainingChart!: ChartOptions;
  performanceChart!: ChartOptions;
  jobPostingsChart!: ChartOptions;

  ngOnInit(): void {
    forkJoin({
      kpis: this.analyticsService.getDashboardKpis(),
      turnover: this.analyticsService.getTurnoverStats(),
      turnoverType: this.analyticsService.getTurnoverTypeStats(),
      salary: this.analyticsService.getSalaryDistributionSummary(),
      funnel: this.analyticsService.getRecruitmentFunnelStats(),
      training: this.analyticsService.getTrainingAnalyticsStats(),
      topPerformers: this.analyticsService.getTopPerformerBenchmarksStats(),
      performance: this.analyticsService.getPerformanceEngagementStats(),
      employees: this.hrService.getAllEmployees(),
      jobPostings: this.hrService.getAllJobPostings()
    }).subscribe(({ kpis, turnover, turnoverType, salary, funnel, training, topPerformers, performance, employees, jobPostings }) => {
      
      this.kpi = kpis;
      this.employees = employees;
      this.jobPostings = jobPostings;
      this.turnoverData = turnover;
      
      this.topPerformers = [...topPerformers]
        .sort((a, b) => (b.avgEngagement ?? 0) - (a.avgEngagement ?? 0))
        .slice(0, 5);

      this.turnoverChart = this.buildTurnoverChart(turnover);
      this.turnoverTypeChart = this.buildTurnoverByTypeChart(turnoverType);
      this.statusDonut = this.buildStatusDonut(kpis);
      this.salaryChart = this.buildSalaryChart(salary);
      this.funnelChart = this.buildFunnelChart(funnel);
      this.trainingChart = this.buildTrainingChart(training);
      this.performanceChart = this.buildPerformanceChart(performance);
      this.jobPostingsChart = this.buildJobPostingsChart(jobPostings);

      this.loading = false;
    });
  }

  private buildTurnoverChart(turnover: DepartmentTurnoverDTO[]): ChartOptions {
    const sortedData = [...turnover].sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0));
    const chartHeight = Math.max(340, sortedData.length * 35);

    return {
      series: [{ name: 'Turnover %', data: sortedData.map(t => t.turnoverRatePct ?? 0) }],
      chart: { type: 'bar', height: chartHeight, ...DARK_THEME_BASE },
      xaxis: { categories: sortedData.map(t => t.businessUnit ?? `ID: ${t.departmentId}`) },
      plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true } },
      dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}%` },
      colors: ['#2dd4bf', '#22d3ee', '#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#fb923c'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `${v.toFixed(1)}%` } },
      legend: { show: false },
    };
  }

  private buildStatusDonut(kpi: KpiSummaryDTO): ChartOptions {
    const active = kpi.activeEmployees ?? 0;
    const total = kpi.totalEmployees ?? 0;
    const terminated = Math.max(0, total - active);

    return {
      series: [active, terminated],
      chart: { type: 'donut', height: 320, ...DARK_THEME_BASE },
      labels: ['Actifs', 'Terminés'],
      colors: ['#2dd4bf', '#f87171'],
      legend: { position: 'bottom', labels: { colors: '#94a3b8' } },
      dataLabels: { enabled: true },
      stroke: { show: false },
      tooltip: { theme: 'dark' },
      responsive: [{ breakpoint: 480, options: { chart: { width: 260 } } }],
    };
  }

  private buildSalaryChart(salary: DepartmentSalarySummaryDTO[]): ChartOptions {
    return {
      series: [{ name: 'Salaire Moyen', data: salary.map(s => Math.round(s.avgSalary ?? 0)) }],
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      xaxis: { categories: salary.map(s => s.businessUnit ?? 'Unknown') },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } },
      dataLabels: { enabled: false },
      colors: ['#38bdf8'],
      fill: {
        type: 'gradient',
        gradient: { shade: 'dark', shadeIntensity: 0.4, gradientToColors: ['#2dd4bf'], opacityFrom: 0.9, opacityTo: 0.6 },
      },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { show: false },
    };
  }

  private buildFunnelChart(funnel: RecruitmentFunnelAtsDTO[]): ChartOptions {
    const totals = funnel.reduce(
      (acc, f) => {
        acc.applications += f.totalApplications ?? 0;
        acc.pending += f.pendingApplications ?? 0;
        acc.hired += f.hiredCount ?? 0;
        acc.rejected += f.rejectedCount ?? 0;
        return acc;
      },
      { applications: 0, pending: 0, hired: 0, rejected: 0 }
    );
    return {
      series: [{ name: 'Candidats', data: [totals.applications, totals.pending, totals.hired, totals.rejected] }],
      chart: { type: 'bar', height: 300, ...DARK_THEME_BASE },
      xaxis: { categories: ['Candidatures', 'En Attente', 'Embauchés', 'Rejetés'] },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '45%', distributed: true } },
      dataLabels: { enabled: true },
      colors: ['#818cf8', '#facc15', '#4ade80', '#f87171'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark' },
      legend: { show: false },
    };
  }

  private buildTrainingChart(training: TrainingAnalyticsDTO[]): ChartOptions {
    const investmentByType = training.reduce((acc, curr) => {
      const type = (curr as any).departmentType || curr.businessUnit || 'Unknown';
      acc[type] = (acc[type] || 0) + (curr.totalTrainingInvestment ?? 0);
      return acc;
    }, {} as Record<string, number>);

    const categories = Object.keys(investmentByType);
    const data = Object.values(investmentByType);

    return {
      series: [{ name: 'Investissement', data }],
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      xaxis: { categories, labels: { hideOverlappingLabels: true, rotate: -45 } },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } },
      dataLabels: { enabled: false },
      colors: ['#a78bfa'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { show: false },
    };
  }

  private buildPerformanceChart(performance: EmployeePerformanceEngagementDTO[]): ChartOptions {
    const allData = [...performance];
    const categories = allData.map(p => p.title ?? p.jobFunction ?? 'Unknown');
    
    const performanceData = allData.map(p => {
      let raw = 0;
      if (typeof p.performanceScore === 'number') raw = p.performanceScore;
      else {
        const parsed = parseFloat(p.performanceScore as unknown as string);
        raw = !isNaN(parsed) ? parsed : (p.avgSatisfactionScore ?? 0);
      }
      return raw > 5 ? Number((raw / 20).toFixed(1)) : Number(raw.toFixed(1));
    });
    
    const engagementData = allData.map(p => {
      const raw = p.avgEngagementScore ?? (p as any).engagementScore ?? (p as any).avgEngagement ?? 0;
      return raw > 5 ? Number((raw / 20).toFixed(1)) : Number(raw.toFixed(1));
    });

    return {
      series: [
        { name: 'Performance', type: 'column', data: performanceData },
        { name: 'Engagement', type: 'line', data: engagementData }
      ],
      chart: { 
        type: 'line', 
        height: 320, 
        width: Math.max(600, allData.length * 45),
        ...DARK_THEME_BASE 
      },
      xaxis: { categories, labels: { rotate: -45, style: { fontSize: '11px' } } },
      yaxis: { min: 0, max: 5 }, 
      plotOptions: { bar: { borderRadius: 4, columnWidth: '40%' } },
      stroke: { width: [0, 3], curve: 'smooth' },
      colors: ['#38bdf8', '#facc15'],
      markers: { size: [0, 5] },
      dataLabels: { enabled: false },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark' },
      legend: { position: 'top', labels: { colors: '#94a3b8' } },
    };
  }

  private buildTurnoverByTypeChart(turnoverTypes: DepartmentTypeTurnoverDTO[]): ChartOptions {
    const sortedData = [...turnoverTypes].sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0));
    return {
      series: [{ name: 'Turnover %', data: sortedData.map(t => t.turnoverRatePct ?? 0) }],
      chart: { type: 'bar', height: 340, ...DARK_THEME_BASE },
      xaxis: { categories: sortedData.map(t => t.departmentType ?? 'Unknown'), labels: { hideOverlappingLabels: true } },
      plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true } },
      dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}%` },
      colors: ['#38bdf8', '#f472b6', '#34d399', '#facc15', '#a78bfa', '#fb923c', '#2dd4bf'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `${v.toFixed(1)}%` } },
      legend: { show: false },
    };
  }

  private buildJobPostingsChart(postings: JobPostingDTO[]): ChartOptions {
    const openPostings = postings.filter(j => !j.status || j.status.toUpperCase() === 'OPEN');
    const deptCounts: { [key: string]: number } = {};
    
    openPostings.forEach(j => {
      const dept = j.departmentName || 'Non assigné';
      deptCounts[dept] = (deptCounts[dept] || 0) + 1;
    });

    const categories = Object.keys(deptCounts);
    const data = Object.values(deptCounts);

    return {
      series: [{ name: 'Postes Ouverts', data }],
      chart: { type: 'bar', height: 300, ...DARK_THEME_BASE },
      xaxis: { categories },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '45%' } },
      colors: ['#38bdf8'],
      dataLabels: { enabled: true },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark' },
      legend: { show: false }
    };
  }
}
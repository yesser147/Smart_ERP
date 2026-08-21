import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';
import {
  NgApexchartsModule, ApexAxisChartSeries, ApexChart, ApexXAxis, ApexYAxis,
  ApexPlotOptions, ApexDataLabels, ApexFill, ApexGrid, ApexTooltip, ApexLegend,
  ApexNonAxisChartSeries, ApexResponsive, ApexMarkers, ApexStroke
} from 'ng-apexcharts';

import { HrService } from '../../../core/services/hr.service';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { EmployeeDTO, DepartmentDTO, JobPostingDTO } from '../../../core/models/hr.model';
import {
  DepartmentTurnoverDTO,
  SalaryDistributionDTO,
  RecruitmentFunnelAtsDTO,
  TrainingAnalyticsDTO,
  AttritionRiskIndicatorsDTO,
  TopPerformerBenchmarksDTO,
  EmployeePerformanceEngagementDTO,
  DepartmentTypeTurnoverDTO
} from '../../../core/models/analytics.model';

export type ChartOptions = {
  series: ApexAxisChartSeries | ApexNonAxisChartSeries;
  chart: ApexChart;
  colors: string[];
  dataLabels: ApexDataLabels;
  tooltip: ApexTooltip;  // <-- Removed the '?'
  legend: ApexLegend;    // <-- Removed the '?'
  
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
  imports: [CommonModule, NgApexchartsModule],
  templateUrl: './hr-dashboard.component.html'
})
export class HrDashboardComponent implements OnInit {
  private hrService = inject(HrService);
  private analyticsService = inject(AnalyticsService);

  loading = true;

  employees: EmployeeDTO[] = [];
  departments: DepartmentDTO[] = [];
  jobPostings: JobPostingDTO[] = [];
  topPerformers: TopPerformerBenchmarksDTO[] = [];

  kpi = {
    totalEmployees: 0,
    activeEmployees: 0,
    departmentCount: 0,
    openJobPostings: 0,
    avgEngagement: 0,
    companyTurnoverRate: 0, // renamed for clarity
    highRiskCount: 0,
  };


  turnoverChart!: ChartOptions;
  turnoverTypeChart!:ChartOptions;
  statusDonut!: ChartOptions;
  salaryChart!: ChartOptions;
  funnelChart!: ChartOptions;
  trainingChart!: ChartOptions;
  riskDonut!: ChartOptions;
  performanceChart!: ChartOptions; // New Chart

  ngOnInit(): void {
    forkJoin({
      employees: this.hrService.getAllEmployees(),
      departments: this.hrService.getAllDepartments(),
      jobPostings: this.hrService.getAllJobPostings(),
      turnover: this.analyticsService.getTurnoverStats(),
      turnoverType:this.analyticsService.getTurnoverTypeStats(),
      salary: this.analyticsService.getSalaryDistributionStats(),
      funnel: this.analyticsService.getRecruitmentFunnelStats(),
      training: this.analyticsService.getTrainingAnalyticsStats(),
      risk: this.analyticsService.getRiskStats(),
      topPerformers: this.analyticsService.getTopPerformerBenchmarksStats(),
      performance: this.analyticsService.getPerformanceEngagementStats() 
    }).subscribe(({ employees, departments, jobPostings, turnover,turnoverType, salary, funnel, training, risk, topPerformers, performance }) => {
      
      this.employees = employees;
      this.departments = departments;
      this.jobPostings = jobPostings;
      this.topPerformers = [...topPerformers]
        .sort((a, b) => (b.avgEngagement ?? 0) - (a.avgEngagement ?? 0))
        .slice(0, 5);

      this.buildKpis(employees, departments, jobPostings, turnover, risk);
      this.turnoverChart = this.buildTurnoverChart(turnover);
      this.turnoverTypeChart=this.buildTurnoverByTypeChart(turnoverType);
      this.statusDonut = this.buildStatusDonut(turnover);
      this.salaryChart = this.buildSalaryChart(salary);
      this.funnelChart = this.buildFunnelChart(funnel);
      this.trainingChart = this.buildTrainingChart(training);
      this.riskDonut = this.buildRiskDonut(risk);
      this.performanceChart = this.buildPerformanceChart(performance);

      this.loading = false;
    });
  }

  private buildKpis(
    employees: EmployeeDTO[],
    departments: DepartmentDTO[],
    jobPostings: JobPostingDTO[],
    turnover: DepartmentTurnoverDTO[],
    risk: AttritionRiskIndicatorsDTO[]
  ) {
    const activeCount = employees.filter(e => e.employeeStatus === 'Active').length;
    
    // LOGIC FIX: Weighted company-wide turnover instead of average of averages
    const totalActive = turnover.reduce((sum, t) => sum + (t.activeCount ?? 0), 0);
    const totalTerminated = turnover.reduce((sum, t) => sum + (t.terminatedCount ?? 0), 0);
    const companyTurnover = totalActive + totalTerminated > 0 
      ? (totalTerminated / (totalActive + totalTerminated)) * 100 
      : 0;

    const avgEngagement = risk.length
      ? risk.reduce((sum, r) => sum + (r.recentEngagement ?? 0), 0) / risk.length
      : 0;

    this.kpi = {
      totalEmployees: employees.length,
      activeEmployees: activeCount,
      departmentCount: departments.length,
      openJobPostings: jobPostings.filter(j => (j.status ?? '').toUpperCase() === 'OPEN').length,
      avgEngagement: Math.round(avgEngagement * 10) / 10,
      companyTurnoverRate: Math.round(companyTurnover * 10) / 10,
      highRiskCount: risk.filter(r => r.heuristicRiskLevel === 'HIGH').length,
    };
  }
  
  private buildTurnoverChart(turnover: DepartmentTurnoverDTO[]): ChartOptions {
    // 1. Sort highest to lowest turnover
    // 2. Slice to keep only the Top 10
    const top10 = [...turnover]
      .sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0))
      .slice(0, 10);

    return {
      series: [{ name: 'Turnover %', data: top10.map(t => t.turnoverRatePct ?? 0) }],
      chart: { type: 'bar', height: 340, ...DARK_THEME_BASE },
      xaxis: { categories: top10.map(t => t.businessUnit ?? 'Unknown') },
      plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true } },
      dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}%` },
      colors: ['#2dd4bf', '#22d3ee', '#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#fb923c'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `${v.toFixed(1)}%` } },
      legend: { show: false },
    };
  }

  private buildStatusDonut(turnover: DepartmentTurnoverDTO[]): ChartOptions {
    const active = turnover.reduce((s, t) => s + (t.activeCount ?? 0), 0);
    const terminated = turnover.reduce((s, t) => s + (t.terminatedCount ?? 0), 0);
    return {
      series: [active, terminated],
      chart: { type: 'donut', height: 320, ...DARK_THEME_BASE },
      labels: ['Active', 'Terminated'],
      colors: ['#2dd4bf', '#f87171'],
      legend: { position: 'bottom', labels: { colors: '#94a3b8' } },
      dataLabels: { enabled: true },
      stroke: { show: false },
      tooltip: { theme: 'dark' },
      responsive: [{ breakpoint: 480, options: { chart: { width: 260 } } }],
    };
  }

  private buildSalaryChart(salary: SalaryDistributionDTO[]): ChartOptions {
    const byDept = new Map<string, { total: number; count: number }>();
    for (const row of salary) {
      const key = row.businessUnit ?? 'Unknown';
      const entry = byDept.get(key) ?? { total: 0, count: 0 };
      entry.total += (row.avgSalary ?? 0) * (row.employeeCount ?? 0);
      entry.count += row.employeeCount ?? 0;
      byDept.set(key, entry);
    }
    const labels = Array.from(byDept.keys());
    const data = labels.map(l => {
      const e = byDept.get(l)!;
      return e.count ? Math.round(e.total / e.count) : 0;
    });
    return {
      series: [{ name: 'Avg Salary', data }],
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      xaxis: { categories: labels },
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
      series: [{ name: 'Candidates', data: [totals.applications, totals.pending, totals.hired, totals.rejected] }],
      chart: { type: 'bar', height: 280, ...DARK_THEME_BASE },
      xaxis: { categories: ['Applications', 'Pending', 'Hired', 'Rejected'] },
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
    // Show top 15 highest investments
    const top15 = [...training]
      .sort((a, b) => (b.totalTrainingInvestment ?? 0) - (a.totalTrainingInvestment ?? 0))
      .slice(0, 15);

    return {
      series: [{ name: 'Investment', data: top15.map(t => t.totalTrainingInvestment ?? 0) }],
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      xaxis: { 
        categories: top15.map(t => t.businessUnit ?? 'Unknown'),
        labels: { hideOverlappingLabels: true, rotate: -45 } // Better label rotation
      },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } },
      dataLabels: { enabled: false },
      colors: ['#a78bfa'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { show: false },
    };
  }

  private buildRiskDonut(risk: AttritionRiskIndicatorsDTO[]): ChartOptions {
    const counts: Record<'HIGH' | 'MEDIUM' | 'LOW', number> = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    for (const r of risk) {
      const level = (r.heuristicRiskLevel ?? 'LOW') as 'HIGH' | 'MEDIUM' | 'LOW';
      counts[level] = (counts[level] ?? 0) + 1;
    }
    return {
      series: [counts.HIGH, counts.MEDIUM, counts.LOW],
      chart: { type: 'donut', height: 320, ...DARK_THEME_BASE },
      labels: ['High Risk', 'Medium Risk', 'Low Risk'],
      colors: ['#f87171', '#facc15', '#4ade80'],
      legend: { position: 'bottom', labels: { colors: '#94a3b8' } },
      dataLabels: { enabled: true },
      stroke: { show: false },
      tooltip: { theme: 'dark' },
      responsive: [{ breakpoint: 480, options: { chart: { width: 260 } } }],
    };
  }

private buildPerformanceChart(performance: EmployeePerformanceEngagementDTO[]): ChartOptions {
    // Take a readable slice of data (Top 15) to prevent the "yellow blob" effect
    const top15 = [...performance]
      .sort((a: any, b: any) => (b.avgPerformanceScore ?? 0) - (a.avgPerformanceScore ?? 0))
      .slice(0, 15);

    const categories = top15.map((p: any) => p.businessUnit ?? 'Unknown');
    const performanceData = top15.map((p: any) => p.avgPerformanceScore ?? 0);
    const engagementData = top15.map((p: any) => p.avgEngagementScore ?? 0);

    return {
      series: [
        { name: 'Performance', type: 'column', data: performanceData },
        { name: 'Engagement', type: 'line', data: engagementData }
      ],
      chart: { type: 'line', height: 320, ...DARK_THEME_BASE },
      xaxis: { 
        categories,
        labels: { hideOverlappingLabels: true, style: { fontSize: '11px' } } // Added text protection
      },
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
    // 1. Sort highest to lowest turnover
    const sortedData = [...turnoverTypes]
      .sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0));

    return {
      series: [{ name: 'Turnover %', data: sortedData.map(t => t.turnoverRatePct ?? 0) }],
      chart: { type: 'bar', height: 340, ...DARK_THEME_BASE },
      xaxis: { 
        categories: sortedData.map(t => t.departmentType ?? 'Unknown'),
        labels: { hideOverlappingLabels: true }
      },
      plotOptions: { 
        bar: { horizontal: true, borderRadius: 4, distributed: true } 
      },
      dataLabels: { 
        enabled: true, 
        formatter: (v: number) => `${Math.round(v)}%` 
      },
      colors: ['#38bdf8', '#f472b6', '#34d399', '#facc15', '#a78bfa', '#fb923c', '#2dd4bf'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { 
        theme: 'dark', 
        y: { formatter: (v: number) => `${v.toFixed(1)}%` } 
      },
      legend: { show: false },
    };
  }
  
}
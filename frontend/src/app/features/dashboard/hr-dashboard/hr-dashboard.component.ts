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
import { AiService } from '../../../core/services/ai.service';
import { EmployeeDTO, JobPostingDTO } from '../../../core/models/hr.model';
import {
  KpiSummaryDTO,
  TopPerformerBenchmarksDTO,
  DepartmentTurnoverDTO,
  DepartmentSalarySummaryDTO,
  RecruitmentFunnelAtsDTO,
  TrainingAnalyticsDTO,
  EmployeePerformanceEngagementDTO,
  DepartmentTypeTurnoverDTO,
  GenderPayGapDTO,
  TimeToHireDTO,
  DepartmentSummaryDTO
} from '../../../core/models/analytics.model';

import { HrOverviewComponent } from '../hr-overview/hr-overview.component';
import { HrTurnoverComponent } from '../hr-turnover/hr-turnover.component';
import { HrCompensationComponent } from '../hr-compensation/hr-compensation.component';
import { HrRecruitmentComponent } from '../hr-recruitment/hr-recruitment.component';
import { HrRetentionComponent } from '../hr-retention/hr-retention.component';
import { HrBudgetAdvisorComponent } from '../hr-budget-advisor/hr-budget-advisor.component';
import { EmployeeListComponent } from '../employee-list/employee-list.component';
import { DepartmentListComponent } from '../department-list/department-list.component';

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
  width: '100%', // follows the container width (sidebar collapse / expand)
};

/** 120000 -> "120k", 850 -> "850" (avoids labels like 120000.0000000000) */
const compactNumber = (v: number): string =>
  Math.abs(v) >= 1000 ? `${Math.round(v / 1000)}k` : `${Math.round(v)}`;

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
    HrRetentionComponent,
    EmployeeListComponent,
    DepartmentListComponent
  ],
  templateUrl: './hr-dashboard.component.html'
})
export class HrDashboardComponent implements OnInit {
  private analyticsService = inject(AnalyticsService);
  private hrService = inject(HrService);
  private aiService = inject(AiService);

  @Input() currentView: string = 'overview';

  loading = true;

  kpi!: KpiSummaryDTO;
  employees: EmployeeDTO[] = [];
  jobPostings: JobPostingDTO[] = [];
  topPerformers: TopPerformerBenchmarksDTO[] = [];
  turnoverData: DepartmentTurnoverDTO[] = [];
  payGapData: GenderPayGapDTO[] = [];
  timeToHireData: TimeToHireDTO[] = [];
  recruitmentSummary: { activeApplications: number; interviewing: number; offered: number } | null = null;
  departmentTypeCount = 0;
  departmentSummary: DepartmentSummaryDTO[] = [];

  // High-risk count from the AI retention endpoint (same source as the Retention page)
  highRiskCount: number | null = null;
  riskIndicative = false;

  turnoverChart!: ChartOptions;
  turnoverTypeChart!: ChartOptions;
  statusDonut!: ChartOptions;
  salaryChart!: ChartOptions;
  funnelChart!: ChartOptions;
  trainingChart!: ChartOptions;
  performanceChart!: ChartOptions;
  jobPostingsChart!: ChartOptions;
  payGapChart!: ChartOptions;

  ngOnInit(): void {
    this.loadRiskSummary();

    forkJoin({
      kpis: this.analyticsService.getDashboardKpis(),
      turnover: this.analyticsService.getTurnoverStats(),
      turnoverType: this.analyticsService.getTurnoverTypeStats(),
      salary: this.analyticsService.getSalaryDistributionSummary(),
      funnel: this.analyticsService.getRecruitmentFunnelStats(),
      training: this.analyticsService.getTrainingAnalyticsStats(),
      topPerformers: this.analyticsService.getTopPerformerBenchmarksStats(),
      performance: this.analyticsService.getPerformanceEngagementStats(),
      payGap: this.analyticsService.getGenderPayGap(),
      timeToHire: this.analyticsService.getTimeToHire(),
      employees: this.hrService.getAllEmployees(),
      jobPostings: this.hrService.getAllJobPostings(),
      departmentSummary: this.analyticsService.getDepartmentSummary()
    }).subscribe(({ kpis, turnover, turnoverType, salary, funnel, training, topPerformers, performance, payGap, timeToHire, employees, jobPostings, departmentSummary }) => {

      this.kpi = kpis;
      this.employees = employees;
      this.jobPostings = jobPostings;
      this.turnoverData = turnover;
      this.payGapData = payGap;
      this.timeToHireData = timeToHire;

      // "Active" = every application that has not been rejected
      const sumOf = (pick: (f: RecruitmentFunnelAtsDTO) => number | undefined) =>
        funnel.reduce((s, f) => s + (pick(f) ?? 0), 0);
      const notRejected =
        sumOf(f => f.appliedCount) + sumOf(f => f.inReviewCount) +
        sumOf(f => f.interviewingCount) + sumOf(f => f.offeredCount);

      this.recruitmentSummary = {
        activeApplications: notRejected,
        interviewing: sumOf(f => f.interviewingCount),
        offered: sumOf(f => f.offeredCount)
      };

      this.departmentTypeCount = new Set(
        departmentSummary.map((d: DepartmentSummaryDTO) => d.departmentType || 'Unclassified')
      ).size;
      this.departmentSummary = departmentSummary;

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
      this.payGapChart = this.buildPayGapChart(payGap);

      this.loading = false;
    });
  }

  /** Separate from the forkJoin so a slow/failed AI call never blocks the dashboard. */
  private loadRiskSummary(): void {
    this.aiService.getRetentionStrategy().subscribe({
      next: (r) => {
        this.highRiskCount = r?.macro_metrics?.high_risk_count ?? null;
        this.riskIndicative = !!r?.model_quality && r.model_quality.level !== 'acceptable';
      },
      error: () => { this.highRiskCount = null; } // Overview falls back to kpi.highRiskCount
    });
  }

  private buildTurnoverChart(turnover: DepartmentTurnoverDTO[]): ChartOptions {
    const sortedData = [...turnover].sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0));
    const chartHeight = Math.max(340, sortedData.length * 35);

    return {
      series: [{ name: 'Turnover %', data: sortedData.map(t => t.turnoverRatePct ?? 0) }],
      chart: { type: 'bar', height: chartHeight, ...DARK_THEME_BASE },
      xaxis: { categories: sortedData.map(t => t.divisionDescription || t.businessUnit || `ID: ${t.departmentId}`) },
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
      labels: ['Active', 'Terminated'],
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
      series: [{ name: 'Average salary', data: salary.map(s => Math.round(s.avgSalary ?? 0)) }],
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      xaxis: { categories: salary.map(s => s.divisionDescription || s.businessUnit || 'Unknown') },
      yaxis: { labels: { formatter: compactNumber } },
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

  /**
   * Cumulative funnel. Each application has ONE current status, so raw counts per
   * status are a distribution, not a funnel. Here everyone who reached a stage is
   * counted in the earlier stages too. Rejected applications are only counted in
   * "Received" because the stage at which they were rejected is not recorded.
   */
  private buildFunnelChart(funnel: RecruitmentFunnelAtsDTO[]): ChartOptions {
    const sumOf = (pick: (f: RecruitmentFunnelAtsDTO) => number | undefined) =>
      funnel.reduce((s, f) => s + (pick(f) ?? 0), 0);

    const applied = sumOf(f => f.appliedCount);
    const inReview = sumOf(f => f.inReviewCount);
    const interviewing = sumOf(f => f.interviewingCount);
    const offered = sumOf(f => f.offeredCount);
    const rejected = sumOf(f => f.rejectedCount);

    const received = applied + inReview + interviewing + offered + rejected;
    const screened = inReview + interviewing + offered;
    const interviewed = interviewing + offered;

    const categories = ['Received', 'Screened', 'Interviewed', 'Offered'];
    const stages = [received, screened, interviewed, offered];

    return {
      series: [{ name: 'Applications', data: stages }],
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      plotOptions: { bar: { horizontal: true, isFunnel: true, distributed: true } as any },
      xaxis: { categories },
      colors: ['#818cf8', '#38bdf8', '#2dd4bf', '#4ade80'],
      dataLabels: {
        enabled: true,
        formatter: (val: number, opts: any) => {
          const pct = received ? ((val / received) * 100).toFixed(0) : '0';
          return `${categories[opts.dataPointIndex]}: ${val} (${pct}%)`;
        },
        dropShadow: { enabled: false }
      },
      fill: { opacity: 0.9 },
      grid: { show: false },
      tooltip: { theme: 'dark' },
      legend: { show: false },
    };
  }

  private buildTrainingChart(training: TrainingAnalyticsDTO[]): ChartOptions {
    const investmentByDivision = training.reduce((acc, curr) => {
      const key = curr.divisionDescription || curr.businessUnit || 'Unknown';
      acc[key] = (acc[key] || 0) + (curr.totalTrainingInvestment ?? 0);
      return acc;
    }, {} as Record<string, number>);

    const categories = Object.keys(investmentByDivision);
    const data = Object.values(investmentByDivision);

    return {
      series: [{ name: 'Investment', data }],
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      xaxis: {
        categories,
        labels: {
          hideOverlappingLabels: false, // show every division, not every other one
          rotate: -45,
          rotateAlways: true,
          trim: true,
          maxHeight: 120,
          style: { fontSize: '10px' }
        }
      },
      yaxis: { labels: { formatter: compactNumber } },
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
    const normalize = (raw: number) => raw > 5 ? Number((raw / 20).toFixed(1)) : Number(raw.toFixed(1));

    const groups = new Map<string, { perfSum: number; engSum: number; count: number }>();
    for (const p of performance) {
      const key = p.title ?? p.jobFunction ?? 'Unknown';
      let raw = 0;
      if (typeof p.performanceScore === 'number') raw = p.performanceScore;
      else {
        const parsed = parseFloat(p.performanceScore as unknown as string);
        raw = !isNaN(parsed) ? parsed : (p.avgSatisfactionScore ?? 0);
      }
      const perf = normalize(raw);
      const eng = normalize(p.avgEngagementScore ?? (p as any).engagementScore ?? (p as any).avgEngagement ?? 0);

      const g = groups.get(key);
      if (g) { g.perfSum += perf; g.engSum += eng; g.count++; }
      else groups.set(key, { perfSum: perf, engSum: eng, count: 1 });
    }

    const categories = [...groups.keys()];
    const performanceData = categories.map(k => Number((groups.get(k)!.perfSum / groups.get(k)!.count).toFixed(1)));
    const engagementData = categories.map(k => Number((groups.get(k)!.engSum / groups.get(k)!.count).toFixed(1)));

    return {
      series: [
        { name: 'Performance', type: 'column', data: performanceData },
        { name: 'Engagement', type: 'line', data: engagementData }
      ],
      chart: { type: 'line', height: 320, ...DARK_THEME_BASE },
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
    const groupCounts: { [key: string]: number } = {};

    openPostings.forEach(j => {
      const groupKey = j.departmentType || j.divisionDescription || j.businessUnit || 'Unassigned';
      groupCounts[groupKey] = (groupCounts[groupKey] || 0) + 1;
    });

    const categories = Object.keys(groupCounts);
    const data = Object.values(groupCounts);

    return {
      series: [{ name: 'Open postings', data }],
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

  /** Groups by division (the real, comparable job-function unit) with the
   * department type appended for context -- business_unit is a site/location
   * code and was dropped from this comparison since it doesn't reflect role
   * or pay-band, and mixing it in would compare unlike jobs against each other. */
  private buildPayGapChart(payGap: GenderPayGapDTO[]): ChartOptions {
    const divisions = [...new Set(payGap.map(p => p.divisionDescription))];
    const genders = [...new Set(payGap.map(p => p.gender))];

    const labelFor = (division: string) => {
      const match = payGap.find(p => p.divisionDescription === division);
      return match?.departmentType ? `${division} (${match.departmentType})` : division;
    };

    const series = genders.map(g => ({
      name: g,
      data: divisions.map(d => {
        const match = payGap.find(p => p.divisionDescription === d && p.gender === g);
        return match ? Math.round(match.avgSalary) : 0;
      })
    }));

    return {
      series,
      chart: { type: 'bar', height: 320, ...DARK_THEME_BASE },
      xaxis: { categories: divisions.map(labelFor), labels: { rotate: -45, hideOverlappingLabels: true } },
      yaxis: { labels: { formatter: compactNumber } },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '55%' } },
      dataLabels: { enabled: false },
      colors: ['#38bdf8', '#f472b6', '#a78bfa'],
      fill: { opacity: 0.9 },
      grid: { borderColor: '#334155', strokeDashArray: 4 },
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { position: 'top', labels: { colors: '#94a3b8' } },
    };
  }
}
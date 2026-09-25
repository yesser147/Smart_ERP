import { Component, Input, OnInit, inject } from '@angular/core';
import {
  ApexAxisChartSeries, ApexChart, ApexDataLabels, ApexFill, ApexGrid, ApexLegend, ApexMarkers,
  ApexNonAxisChartSeries, ApexPlotOptions, ApexResponsive, ApexStroke, ApexTooltip, ApexXAxis, ApexYAxis
} from 'ng-apexcharts';

import { AnalyticsService, DashboardData } from '../../../core/services/analytics.service';
import { AiService } from '../../../core/services/ai.service';
import { JobPostingDTO } from '../../../core/models/hr.model';
import {
  DepartmentSalarySummaryDTO, DepartmentSummaryDTO, DepartmentTypeTurnoverDTO, EmployeePerformanceEngagementDTO,
  GenderPayGapDTO, KpiSummaryDTO, RecruitmentFunnelAtsDTO, RecruitmentSummary, TimeToHireDTO, TopPerformerBenchmarksDTO, TrainingAnalyticsDTO
} from '../../../core/models/analytics.model';
import { DARK_CHART, GRID, PALETTE, compactNumber } from '../../../shared/utils/chart-theme';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

import { HrOverviewComponent } from '../hr-overview/hr-overview.component';
import { HrTurnoverComponent } from '../hr-turnover/hr-turnover.component';
import { HrCompensationComponent } from '../hr-compensation/hr-compensation.component';
import { HrRecruitmentComponent } from '../hr-recruitment/hr-recruitment.component';

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

export type AnalyticsView = 'overview' | 'turnover' | 'compensation' | 'recruitment-analytics';

const HEADERS: Record<AnalyticsView, { title: string; subtitle: string; icon: string }> = {
  overview: { title: 'Overview', subtitle: 'Workforce KPIs at a glance', icon: 'squares' },
  turnover: { title: 'Turnover', subtitle: 'Who leaves, where, and how long people stay', icon: 'arrow-path' },
  compensation: { title: 'Compensation & performance', subtitle: 'Salaries, training investment, pay equity and engagement', icon: 'banknotes' },
  'recruitment-analytics': { title: 'Recruitment & training', subtitle: 'Pipeline health, time to hire and open roles', icon: 'chart-bar' },
};

/** The four analytics pages. The data is loaded once (AnalyticsService caches it),
 *  so switching between them in the sidebar is instant. */
@Component({
  selector: 'app-analytics-page',
  standalone: true,
  imports: [PageHeaderComponent, IconComponent, HrOverviewComponent, HrTurnoverComponent, HrCompensationComponent, HrRecruitmentComponent],
  templateUrl: './analytics-page.component.html'
})
export class AnalyticsPageComponent implements OnInit {
  private analytics = inject(AnalyticsService);
  private ai = inject(AiService);

  /** From the route data (withComponentInputBinding). */
  @Input() view: AnalyticsView = 'overview';

  loading = true;
  loadError = false;

  kpi!: KpiSummaryDTO;
  jobPostings: JobPostingDTO[] = [];
  topPerformers: TopPerformerBenchmarksDTO[] = [];
  recruitmentSummary: RecruitmentSummary | null = null;
  departmentTypeCount = 0;
  departmentSummary: DepartmentSummaryDTO[] = [];
  highRiskCount: number | null = null;
  riskIndicative = false;

  turnoverTypeChart!: ChartOptions;
  statusDonut!: ChartOptions;
  salaryChart!: ChartOptions;
  funnelChart!: ChartOptions;
  trainingChart!: ChartOptions;
  performanceChart!: ChartOptions;
  jobPostingsChart!: ChartOptions;
  payGapChart!: ChartOptions;

  get header() {
    return HEADERS[this.view] ?? HEADERS.overview;
  }

  ngOnInit(): void {
    this.load();
    if (this.view === 'overview') this.loadRiskSummary();
  }

  refresh(): void {
    this.analytics.invalidate();
    this.load();
  }

  private load(): void {
    this.loading = true;
    this.loadError = false;
    this.analytics.dashboard().subscribe({
      next: data => {
        this.build(data);
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.loadError = true;
      }
    });
  }

  private build(d: DashboardData): void {
    this.kpi = d.kpis;
    this.jobPostings = d.jobPostings;
    this.departmentSummary = d.departmentSummary;
    this.departmentTypeCount = new Set(d.departmentSummary.map(x => x.departmentType || 'Unclassified')).size;
    this.topPerformers = [...d.topPerformers].sort((a, b) => (b.avgEngagement ?? 0) - (a.avgEngagement ?? 0));
    this.recruitmentSummary = this.summarizeRecruitment(d.funnel, d.timeToHire);

    this.turnoverTypeChart = this.buildTurnoverByTypeChart(d.turnoverType);
    this.statusDonut = this.buildStatusDonut(d.kpis);
    this.salaryChart = this.buildSalaryChart(d.salary);
    this.funnelChart = this.buildFunnelChart(d.funnel);
    this.trainingChart = this.buildTrainingChart(d.training);
    this.performanceChart = this.buildPerformanceChart(d.performance);
    this.jobPostingsChart = this.buildJobPostingsChart(d.jobPostings);
    this.payGapChart = this.buildPayGapChart(d.payGap);
  }

  /** Separate from the main load so a slow AI engine never blocks the page (ML only, no LLM). */
  private loadRiskSummary(): void {
    this.ai.getRetentionRiskScores().subscribe({
      next: r => {
        this.highRiskCount = r?.high_risk_count ?? null;
        this.riskIndicative = !!r?.model_quality && r.model_quality.level !== 'acceptable';
      },
      error: () => { this.highRiskCount = null; } // shown as "—"
    });
  }

  private summarizeRecruitment(funnel: RecruitmentFunnelAtsDTO[], timeToHire: TimeToHireDTO[]): RecruitmentSummary {
    const sum = (pick: (f: RecruitmentFunnelAtsDTO) => number | undefined) => funnel.reduce((s, f) => s + (pick(f) ?? 0), 0);
    const hires = timeToHire.reduce((s, t) => s + (t.hiredCount ?? 0), 0);
    const weightedDays = timeToHire.reduce((s, t) => s + (t.avgDaysToHire ?? 0) * (t.hiredCount ?? 0), 0);
    return {
      // "active" = every application that was not rejected
      activeApplications: sum(f => f.appliedCount) + sum(f => f.inReviewCount) + sum(f => f.interviewingCount) + sum(f => f.offeredCount),
      interviewing: sum(f => f.interviewingCount),
      offered: sum(f => f.offeredCount),
      avgDaysToHire: hires ? weightedDays / hires : null,
      hires,
    };
  }

  // ------------------------------------------------------------------ charts

  private buildStatusDonut(kpi: KpiSummaryDTO): ChartOptions {
    const active = kpi.activeEmployees ?? 0;
    const left = Math.max(0, (kpi.totalEmployees ?? 0) - active);
    return {
      series: [active, left],
      chart: { type: 'donut', height: 300, ...DARK_CHART },
      labels: ['Active', 'Left the company'],
      colors: ['#38bdf8', '#334155'],
      legend: { position: 'bottom', labels: { colors: '#94a3b8' } },
      dataLabels: { enabled: false },
      plotOptions: { pie: { donut: { size: '72%', labels: { show: true, total: { show: true, label: 'Employees', color: '#94a3b8' }, value: { color: '#fff' } } } } },
      stroke: { show: false },
      tooltip: { theme: 'dark' },
    };
  }

  private buildTurnoverByTypeChart(rows: DepartmentTypeTurnoverDTO[]): ChartOptions {
    const sorted = [...rows].sort((a, b) => (b.turnoverRatePct ?? 0) - (a.turnoverRatePct ?? 0));
    return {
      series: [{ name: 'Turnover %', data: sorted.map(t => t.turnoverRatePct ?? 0) }],
      chart: { type: 'bar', height: 320, ...DARK_CHART },
      xaxis: { categories: sorted.map(t => t.departmentType ?? 'Unknown') },
      plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '60%', distributed: true } },
      dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}%` },
      colors: PALETTE,
      grid: GRID,
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `${v.toFixed(1)}%` } },
      legend: { show: false },
    };
  }

  /** Horizontal bars of the top N (a vertical axis of ~100 teams is unreadable). */
  private topBars(entries: [string, number][], name: string, color: string, n = 15): ChartOptions {
    const top = [...entries].sort((a, b) => b[1] - a[1]).slice(0, n);
    return {
      series: [{ name, data: top.map(e => Math.round(e[1])) }],
      chart: { type: 'bar', height: Math.max(300, top.length * 26), ...DARK_CHART },
      xaxis: { categories: top.map(e => e[0]), labels: { formatter: (v: any) => compactNumber(Number(v)) } },
      plotOptions: { bar: { horizontal: true, borderRadius: 3, barHeight: '65%' } },
      dataLabels: { enabled: false },
      colors: [color],
      grid: GRID,
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { show: false },
    };
  }

  private buildSalaryChart(salary: DepartmentSalarySummaryDTO[]): ChartOptions {
    return this.topBars(salary.map(s => [s.divisionDescription || s.businessUnit || 'Unknown', s.avgSalary ?? 0]), 'Average salary', '#38bdf8');
  }

  /**
   * Cumulative funnel: each application has ONE current status, so everyone who reached
   * a stage is also counted in the earlier ones. Rejected applications only count in
   * "Received" (the stage of rejection isn't stored for the imported data).
   */
  private buildFunnelChart(funnel: RecruitmentFunnelAtsDTO[]): ChartOptions {
    const sum = (pick: (f: RecruitmentFunnelAtsDTO) => number | undefined) => funnel.reduce((s, f) => s + (pick(f) ?? 0), 0);
    const inReview = sum(f => f.inReviewCount);
    const interviewing = sum(f => f.interviewingCount);
    const offered = sum(f => f.offeredCount);
    const received = sum(f => f.appliedCount) + inReview + interviewing + offered + sum(f => f.rejectedCount);
    const categories = ['Received', 'Screened', 'Interviewed', 'Offered'];
    const stages = [received, inReview + interviewing + offered, interviewing + offered, offered];

    return {
      series: [{ name: 'Applications', data: stages }],
      chart: { type: 'bar', height: 300, ...DARK_CHART },
      plotOptions: { bar: { horizontal: true, isFunnel: true, distributed: true, barHeight: '80%' } as any },
      xaxis: { categories },
      colors: ['#818cf8', '#38bdf8', '#2dd4bf', '#4ade80'],
      dataLabels: {
        enabled: true,
        formatter: (val: number, opts: any) =>
          `${categories[opts.dataPointIndex]}: ${val} (${received ? Math.round((val / received) * 100) : 0}%)`,
        dropShadow: { enabled: false }
      },
      grid: { show: false },
      tooltip: { theme: 'dark' },
      legend: { show: false },
    };
  }

  private buildTrainingChart(training: TrainingAnalyticsDTO[]): ChartOptions {
    const byTeam = training.reduce((acc, t) => {
      const key = t.divisionDescription || t.businessUnit || 'Unknown';
      acc[key] = (acc[key] || 0) + (t.totalTrainingInvestment ?? 0);
      return acc;
    }, {} as Record<string, number>);
    return this.topBars(Object.entries(byTeam), 'Investment', '#a78bfa');
  }

  private buildPerformanceChart(performance: EmployeePerformanceEngagementDTO[]): ChartOptions {
    const toFive = (raw: number) => Number((raw > 5 ? raw / 20 : raw).toFixed(1));
    const groups = new Map<string, { perf: number; eng: number; n: number }>();
    for (const p of performance) {
      const key = p.title ?? p.jobFunction ?? 'Unknown';
      const parsed = parseFloat(p.performanceScore as unknown as string);
      const perf = toFive(!isNaN(parsed) ? parsed : (p.avgSatisfactionScore ?? 0));
      const eng = toFive(p.avgEngagementScore ?? 0);
      const g = groups.get(key) ?? { perf: 0, eng: 0, n: 0 };
      g.perf += perf; g.eng += eng; g.n++;
      groups.set(key, g);
    }
    const categories = [...groups.keys()];
    const avg = (k: string, f: 'perf' | 'eng') => Number((groups.get(k)![f] / groups.get(k)!.n).toFixed(1));

    return {
      series: [
        { name: 'Performance', type: 'column', data: categories.map(k => avg(k, 'perf')) },
        { name: 'Engagement', type: 'line', data: categories.map(k => avg(k, 'eng')) }
      ],
      chart: { type: 'line', height: 340, ...DARK_CHART },
      xaxis: { categories, labels: { rotate: -45, style: { fontSize: '11px' } } },
      yaxis: { min: 0, max: 5 },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '40%' } },
      stroke: { width: [0, 3], curve: 'smooth' },
      colors: ['#38bdf8', '#facc15'],
      markers: { size: [0, 4] },
      dataLabels: { enabled: false },
      grid: GRID,
      tooltip: { theme: 'dark' },
      legend: { position: 'top', labels: { colors: '#94a3b8' } },
    };
  }

  private buildJobPostingsChart(postings: JobPostingDTO[]): ChartOptions {
    const counts: Record<string, number> = {};
    postings.filter(j => (j.status ?? 'OPEN').toUpperCase() === 'OPEN').forEach(j => {
      const key = j.departmentType || j.divisionDescription || 'Unassigned';
      counts[key] = (counts[key] || 0) + 1;
    });
    return {
      series: [{ name: 'Open postings', data: Object.values(counts) }],
      chart: { type: 'bar', height: 300, ...DARK_CHART },
      xaxis: { categories: Object.keys(counts) },
      plotOptions: { bar: { borderRadius: 4, columnWidth: '45%' } },
      colors: ['#38bdf8'],
      dataLabels: { enabled: true },
      grid: GRID,
      tooltip: { theme: 'dark' },
      legend: { show: false }
    };
  }

  /** Average salary per department and gender, weighted by headcount, with the gap in the labels. */
  private buildPayGapChart(payGap: GenderPayGapDTO[]): ChartOptions {
    const departments = [...new Set(payGap.map(p => p.departmentType || 'Unknown'))].sort();
    const genders = [...new Set(payGap.map(p => p.gender))].sort();
    const avg = (dept: string, gender: string) => {
      const rows = payGap.filter(p => (p.departmentType || 'Unknown') === dept && p.gender === gender);
      const n = rows.reduce((s, r) => s + (r.employeeCount || 0), 0);
      return n ? Math.round(rows.reduce((s, r) => s + r.avgSalary * (r.employeeCount || 0), 0) / n) : 0;
    };
    const label = (dept: string) => {
      const [a, b] = genders.map(g => avg(dept, g));
      if (genders.length !== 2 || !a || !b) return dept;
      const gap = ((a - b) / Math.max(a, b)) * 100;
      return `${dept} (gap ${Math.abs(gap).toFixed(1)}%)`;
    };
    return {
      series: genders.map(g => ({ name: g, data: departments.map(d => avg(d, g)) })),
      chart: { type: 'bar', height: 320, ...DARK_CHART },
      xaxis: { categories: departments.map(label) },
      yaxis: { labels: { formatter: compactNumber } },
      plotOptions: { bar: { borderRadius: 3, columnWidth: '45%' } },
      dataLabels: { enabled: true, formatter: (v: number) => compactNumber(v), style: { fontSize: '10px' } },
      colors: ['#f472b6', '#38bdf8', '#a78bfa'],
      grid: GRID,
      tooltip: { theme: 'dark', y: { formatter: (v: number) => `$${v.toLocaleString()}` } },
      legend: { position: 'top', labels: { colors: '#94a3b8' } },
    };
  }
}

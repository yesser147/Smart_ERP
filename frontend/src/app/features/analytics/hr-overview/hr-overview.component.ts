import { Component, Input } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NgApexchartsModule } from 'ng-apexcharts';
import { KpiSummaryDTO, RecruitmentSummary, TopPerformerBenchmarksDTO } from '../../../core/models/analytics.model';
import { StatCardComponent } from '../../../shared/components/stat-card/stat-card.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

interface PerformerRow { title: string; performanceScore: string; avgEngagement: number; count: number; }

@Component({
  selector: 'app-hr-overview',
  standalone: true,
  imports: [DecimalPipe, RouterLink, NgApexchartsModule, StatCardComponent, IconComponent],
  templateUrl: './hr-overview.component.html'
})
export class HrOverviewComponent {
  @Input() kpi!: KpiSummaryDTO;
  @Input() statusDonut: any;
  @Input() recruitmentSummary: RecruitmentSummary | null = null;
  @Input() departmentTypeCount = 0;
  /** From the ML retention model (same source as the Retention page). */
  @Input() highRiskCount: number | null = null;
  @Input() riskIndicative = false;

  performers: PerformerRow[] = [];

  @Input() set topPerformers(list: TopPerformerBenchmarksDTO[]) {
    // one row per role, averaged
    const map = new Map<string, PerformerRow>();
    for (const item of list ?? []) {
      const title = item.title || item.jobFunction || 'N/A';
      const engagement = this.toFive(item.avgEngagement);
      const row = map.get(title);
      if (row) {
        row.avgEngagement = (row.avgEngagement * row.count + engagement) / (row.count + 1);
        row.count++;
      } else {
        map.set(title, { title, performanceScore: item.performanceScore || 'N/A', avgEngagement: engagement, count: 1 });
      }
    }
    this.performers = [...map.values()].slice(0, 6);
  }

  toFive(value: number | undefined): number {
    const v = value ?? 0;
    return v > 5 ? v / 20 : v;
  }

  get riskValue(): string | number {
    return this.highRiskCount ?? '—';
  }
}

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import { KpiSummaryDTO, TopPerformerBenchmarksDTO } from '../../../core/models/analytics.model';

@Component({
  selector: 'app-hr-overview',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule],
  templateUrl: './hr-overview.component.html'
})
export class HrOverviewComponent {
  @Input() kpi!: KpiSummaryDTO;
  @Input() statusDonut: any;
  @Input() topPerformers: TopPerformerBenchmarksDTO[] = [];
  @Input() recruitmentSummary: { activeApplications: number; interviewing: number; offered: number } | null = null;
  @Input() budgetAlertCount: number = 0;
  @Input() departmentTypeCount: number = 0;

  normalizedEngagement(value: number | undefined): number {
    const v = value ?? 0;
    return v > 5 ? v / 20 : v;
  }

  /** Collapses duplicate titles into one row with a count, so "Accountant I"
   * appearing 3 times among top performers reads as "Accountant I ×3"
   * instead of three identical-looking rows. */
  get dedupedTopPerformers(): { title: string; performanceScore: string; avgEngagement: number; count: number }[] {
    const map = new Map<string, { title: string; performanceScore: string; avgEngagement: number; count: number }>();

    for (const item of this.topPerformers) {
      const title = item.title || item.jobFunction || 'N/A';
      const engagement = this.normalizedEngagement(item.avgEngagement);
      const existing = map.get(title);
      if (existing) {
        existing.count++;
        existing.avgEngagement = (existing.avgEngagement * (existing.count - 1) + engagement) / existing.count;
      } else {
        map.set(title, {
          title,
          performanceScore: item.performanceScore || 'N/A',
          avgEngagement: engagement,
          count: 1
        });
      }
    }

    return Array.from(map.values()).slice(0, 5);
  }
}
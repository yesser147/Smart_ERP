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
}
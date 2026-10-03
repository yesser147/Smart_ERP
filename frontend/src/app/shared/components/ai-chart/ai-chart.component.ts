import { Component, Input, OnChanges } from '@angular/core';
import { NgApexchartsModule } from 'ng-apexcharts';
import { ChartSpec } from '../../../core/models/ai.model';
import { buildChart } from '../../utils/chart-spec';

/** Draws a chart chosen by the AI (a ChartSpec) from query rows. Used in the
 *  assistant and in the dashboard's "My charts". */
@Component({
  selector: 'app-ai-chart',
  standalone: true,
  imports: [NgApexchartsModule],
  template: `
    @if (options) {
      <apx-chart [series]="options.series" [chart]="options.chart" [labels]="options.labels" [xaxis]="options.xaxis"
                 [yaxis]="options.yaxis" [colors]="options.colors" [plotOptions]="options.plotOptions"
                 [stroke]="options.stroke" [markers]="options.markers" [dataLabels]="options.dataLabels"
                 [grid]="options.grid" [legend]="options.legend" [tooltip]="options.tooltip" />
    }
  `
})
export class AiChartComponent implements OnChanges {
  @Input({ required: true }) spec!: ChartSpec;
  @Input({ required: true }) rows: Record<string, unknown>[] = [];
  @Input() height = 260;

  options: any = null;

  ngOnChanges(): void {
    this.options = this.spec && this.rows?.length ? buildChart(this.spec, this.rows, this.height) : null;
  }
}

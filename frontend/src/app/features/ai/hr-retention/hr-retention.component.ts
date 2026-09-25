import { Component, OnInit, inject } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AiService } from '../../../core/services/ai.service';
import { AtRiskEmployee } from '../../../core/models/ai.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { StatCardComponent } from '../../../shared/components/stat-card/stat-card.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { errorMessage } from '../../../shared/utils/errors';
import { featureLabel } from '../../../shared/utils/labels';

@Component({
  selector: 'app-hr-retention',
  standalone: true,
  imports: [DatePipe, DecimalPipe, RouterLink, PageHeaderComponent, StatCardComponent, IconComponent, MarkdownPipe],
  templateUrl: './hr-retention.component.html'
})
export class HrRetentionComponent implements OnInit {
  private ai = inject(AiService);

  loading = true;
  error: string | null = null;
  data: any = null;
  atRisk: AtRiskEmployee[] = [];
  showQualityDetails = false;
  readonly generatedAt = new Date();
  readonly featureLabel = featureLabel;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.ai.getRetentionStrategy().subscribe({
      next: res => { this.data = res; this.loading = false; },
      error: err => { this.error = errorMessage(err, 'The retention strategy could not be generated.'); this.loading = false; }
    });
    this.ai.getAtRiskEmployees(15).subscribe({ next: list => this.atRisk = list, error: () => this.atRisk = [] });
  }

  get quality(): string {
    return this.data?.model_quality?.level ?? 'unknown';
  }

  get thresholdPct(): number {
    return Math.round((this.data?.macro_metrics?.risk_threshold ?? this.data?.model_quality?.risk_threshold ?? 0.5) * 100);
  }

  /** Browser print dialog: "Save as PDF" gives the report as a file. */
  print(): void {
    window.print();
  }
}

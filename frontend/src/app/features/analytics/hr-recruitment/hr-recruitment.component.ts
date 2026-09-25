import { Component, Input } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NgApexchartsModule } from 'ng-apexcharts';
import { JobPostingDTO } from '../../../core/models/hr.model';
import { RecruitmentSummary } from '../../../core/models/analytics.model';
import { StatCardComponent } from '../../../shared/components/stat-card/stat-card.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

@Component({
  selector: 'app-hr-recruitment',
  standalone: true,
  imports: [DecimalPipe, RouterLink, NgApexchartsModule, StatCardComponent, IconComponent],
  templateUrl: './hr-recruitment.component.html'
})
export class HrRecruitmentComponent {
  @Input() funnelChart: any;
  @Input() jobPostingsChart: any;
  @Input() jobPostings: JobPostingDTO[] = [];
  @Input() summary: RecruitmentSummary | null = null;

  get openJobs(): number {
    return this.jobPostings.filter(j => (j.status ?? 'OPEN').toUpperCase() === 'OPEN').length;
  }

  get applicants(): number {
    return this.jobPostings.reduce((s, j) => s + (j.applicantCount ?? 0), 0);
  }
}

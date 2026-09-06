import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import { JobPostingDTO } from '../../../core/models/hr.model';

@Component({
  selector: 'app-hr-recruitment',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule],
  templateUrl: './hr-recruitment.component.html'
})
export class HrRecruitmentComponent {
  @Input() funnelChart: any;
  @Input() jobPostingsChart: any;
  @Input() jobPostings: JobPostingDTO[] = [];

  get openJobsCount(): number {
    return this.jobPostings.filter(j => !j.status || j.status.toUpperCase() === 'OPEN').length;
  }
}
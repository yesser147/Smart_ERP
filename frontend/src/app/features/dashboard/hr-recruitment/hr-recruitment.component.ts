import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import { JobPostingDTO } from '../../../core/models/hr.model';
import { TimeToHireDTO } from '../../../core/models/analytics.model'; // NEW
import { CandidateMatchComponent } from '../candidate-match/candidate-match.component';

@Component({
  selector: 'app-hr-recruitment',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, CandidateMatchComponent],
  templateUrl: './hr-recruitment.component.html'
})
export class HrRecruitmentComponent {
  @Input() funnelChart: any;
  @Input() jobPostingsChart: any;
  @Input() jobPostings: JobPostingDTO[] = [];
  @Input() timeToHireData: TimeToHireDTO[] = []; // NEW

  get openJobsCount(): number {
    return this.jobPostings.filter(j => !j.status || j.status.toUpperCase() === 'OPEN').length;
  }
}
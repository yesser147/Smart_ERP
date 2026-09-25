import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { ApplyFormComponent, ApplyJobOption } from '../../careers/apply-form/apply-form.component';

/** HR enters an application received by e-mail, at a fair, etc. */
@Component({
  selector: 'app-job-application-form',
  standalone: true,
  imports: [RouterLink, PageHeaderComponent, ApplyFormComponent],
  template: `
    <div class="erp-page max-w-3xl">
      <app-page-header title="New application" icon="user-plus"
                       subtitle="Enter an application received outside the careers page; the CV is analysed automatically"
                       backLink="/dashboard/applicants" backLabel="Applicants" />
      @if (message) {
        <div class="erp-alert-success items-center justify-between">
          <span>{{ message }}</span>
          <a routerLink="/dashboard/applicants" class="erp-btn-secondary erp-btn-sm">See applicants</a>
        </div>
      }
      <div class="erp-card p-6">
        <app-apply-form [jobs]="jobs" [jobId]="jobId" (submitted)="message = $event" />
      </div>
    </div>
  `
})
export class JobApplicationFormComponent implements OnInit {
  private hr = inject(HrService);
  private route = inject(ActivatedRoute);

  jobs: ApplyJobOption[] = [];
  jobId: number | null = null;
  message: string | null = null;

  ngOnInit(): void {
    const id = this.route.snapshot.queryParamMap.get('jobId');
    this.jobId = id ? Number(id) : null;
    this.hr.getAllJobPostings().subscribe(jobs =>
      this.jobs = jobs.filter(j => j.status === 'OPEN')
        .map(j => ({ jobId: j.jobId, title: j.title, department: j.departmentType })));
  }
}

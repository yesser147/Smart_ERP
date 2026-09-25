import { Component, OnInit, inject } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { DepartmentSummaryDTO } from '../../../core/models/analytics.model';
import { JobPostingDTO } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { StatCardComponent } from '../../../shared/components/stat-card/stat-card.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';

/** One team: headcount, pay, turnover, training and its job openings. */
@Component({
  selector: 'app-department-detail',
  standalone: true,
  imports: [DecimalPipe, RouterLink, PageHeaderComponent, StatCardComponent, StatusBadgeComponent],
  templateUrl: './department-detail.component.html'
})
export class DepartmentDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private analytics = inject(AnalyticsService);

  id!: number;
  team: DepartmentSummaryDTO | null = null;
  jobs: JobPostingDTO[] = [];
  applications = 0;
  trainingInvestment = 0;
  trainedEmployees = 0;
  loading = true;
  error = false;

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.analytics.dashboard().subscribe({
      next: d => {
        this.team = d.departmentSummary.find(t => t.departmentId === this.id) ?? null;
        this.jobs = d.jobPostings.filter(j => j.departmentId === this.id)
          .sort((a, b) => (a.status === 'OPEN' ? -1 : 1) - (b.status === 'OPEN' ? -1 : 1));
        this.applications = d.funnel.filter(f => f.departmentId === this.id).reduce((s, f) => s + (f.totalApplications || 0), 0);
        const training = d.training.filter(t => t.departmentId === this.id);
        this.trainingInvestment = training.reduce((s, t) => s + (t.totalTrainingInvestment || 0), 0);
        this.trainedEmployees = training.reduce((s, t) => s + (t.trainedEmployeesCount || 0), 0);
        this.error = !this.team;
        this.loading = false;
      },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  get openJobs(): number {
    return this.jobs.filter(j => j.status === 'OPEN').length;
  }
}

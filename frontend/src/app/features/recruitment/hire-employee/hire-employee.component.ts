import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { ApplicantDTO, DepartmentDTO, JobPostingDTO } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

@Component({
  selector: 'app-hire-employee',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, PageHeaderComponent, IconComponent],
  templateUrl: './hire-employee.component.html'
})
export class HireEmployeeComponent implements OnInit {
  private fb = inject(NonNullableFormBuilder);
  private hr = inject(HrService);
  private analytics = inject(AnalyticsService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  applicantId!: number;
  jobApplicationId: string | null = null;
  jobId: number | null = null;

  applicant = signal<ApplicantDTO | null>(null);
  teams = signal<DepartmentDTO[]>([]);
  job = signal<JobPostingDTO | null>(null);
  submitting = signal(false);
  error = signal<string | null>(null);
  done = signal<{ employeeId: number; email: string; activationEmailSent: boolean } | null>(null);

  form = this.fb.group({
    departmentId: [null as number | null, Validators.required],
    title: ['', Validators.required],
    employeeType: ['Full-time', Validators.required],
    employeeClassificationType: ['Exempt', Validators.required],
    jobFunction: ['', Validators.required],
    state: ['', Validators.required],
    location: ['', Validators.required],
    startDate: [new Date().toISOString().slice(0, 10), Validators.required],
    salary: [null as number | null, [Validators.required, Validators.min(1)]],
    roleName: ['ROLE_EMPLOYEE', Validators.required]
  });

  ngOnInit(): void {
    this.applicantId = Number(this.route.snapshot.paramMap.get('applicantId'));
    this.jobApplicationId = this.route.snapshot.queryParamMap.get('jobApplicationId');
    const jobId = this.route.snapshot.queryParamMap.get('jobId');
    this.jobId = jobId ? Number(jobId) : null;

    this.hr.getApplicantById(this.applicantId).subscribe({
      next: a => {
        this.applicant.set(a);
        if (a.state) this.form.patchValue({ state: a.state });
      },
      error: () => this.error.set('This applicant does not exist.')
    });

    this.hr.getAllDepartments().subscribe(t => this.teams.set(t));

    if (this.jobId !== null) {
      this.hr.getJobPosting(this.jobId).subscribe(job => {
        this.job.set(job);
        // prefilled from the opening, still editable
        this.form.patchValue({
          departmentId: job.departmentId,
          title: job.title,
          jobFunction: job.departmentType ?? '',
          location: job.location ?? '',
          salary: job.offeredSalaryMin != null && job.offeredSalaryMax != null
            ? Math.round((job.offeredSalaryMin + job.offeredSalaryMax) / 2 / 1000) * 1000
            : job.offeredSalaryMin ?? null,
        });
      });
    }
  }

  teamLabel(t: DepartmentDTO): string {
    return `${t.departmentType} · ${t.divisionDescription} (${t.businessUnit})`;
  }

  invalid(name: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[name];
    return c.invalid && c.touched;
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.hr.hireApplicant(this.applicantId, { ...this.form.getRawValue(), jobApplicationId: this.jobApplicationId }).subscribe({
      next: res => {
        this.submitting.set(false);
        this.done.set(res);
        this.analytics.invalidate();
      },
      error: err => {
        this.submitting.set(false);
        this.error.set(errorMessage(err, 'The employee could not be created.'));
      }
    });
  }

  openEmployee(): void {
    const res = this.done();
    if (res) this.router.navigate(['/dashboard/employee', res.employeeId]);
  }
}

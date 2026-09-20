import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { ApplicantDTO, DepartmentDTO, JobPostingDTO } from '../../../core/models/hr.model';

@Component({
  selector: 'app-hire-employee',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './hire-employee.component.html'
})
export class HireEmployeeComponent implements OnInit {
  private fb = inject(NonNullableFormBuilder);
  private hrService = inject(HrService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  applicantId!: number;
  jobApplicationId: string | null = null;
  jobId: number | null = null;

  applicant = signal<ApplicantDTO | null>(null);
  departments = signal<DepartmentDTO[]>([]);
  job = signal<JobPostingDTO | null>(null);

  isLoading = signal<boolean>(false);
  isSubmitting = signal<boolean>(false);
  successMessage = signal<string | null>(null);
  errorMessage = signal<string | null>(null);

  hireForm = this.fb.group({
    departmentId: [null as number | null, [Validators.required]],
    title: ['', [Validators.required]],
    employeeType: ['Full-time', [Validators.required]],
    employeeClassificationType: ['Exempt', [Validators.required]],
    jobFunction: ['', [Validators.required]],
    state: ['', [Validators.required]],
    location: ['', [Validators.required]],
    startDate: ['', [Validators.required]],
    salary: [0, [Validators.required, Validators.min(1)]],
    roleName: ['ROLE_EMPLOYEE', [Validators.required]]
  });

  ngOnInit(): void {
    this.applicantId = Number(this.route.snapshot.paramMap.get('applicantId'));
    this.jobApplicationId = this.route.snapshot.queryParamMap.get('jobApplicationId');
    const jobIdParam = this.route.snapshot.queryParamMap.get('jobId');
    this.jobId = jobIdParam ? Number(jobIdParam) : null;

    this.isLoading.set(true);
    this.hrService.getApplicantById(this.applicantId).subscribe({
      next: (a) => { this.applicant.set(a); this.isLoading.set(false); },
      error: () => { this.errorMessage.set('Candidat introuvable.'); this.isLoading.set(false); }
    });

    if (this.jobId !== null) {
      this.hrService.getAllJobPostings().subscribe(jobs => {
        const job = jobs.find(j => j.jobId === this.jobId) ?? null;
        this.job.set(job);
        if (job) {
          // department is fixed by the posting; title/location are prefilled but editable
          this.hireForm.patchValue({
            departmentId: job.departmentId,
            title: job.title,
            location: job.location ?? ''
          });
        } else {
          this.loadDepartments();
        }
      });
    } else {
      this.loadDepartments();   // opened without a job: keep the manual picker
    }
  }

  private loadDepartments(): void {
    this.hrService.getAllDepartments().subscribe(d => this.departments.set(d));
  }

  onSubmit(): void {
    if (this.hireForm.invalid) {
      this.hireForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    const payload = { ...this.hireForm.getRawValue(), jobApplicationId: this.jobApplicationId };

    this.hrService.hireApplicant(this.applicantId, payload).subscribe({
      next: (res) => {
        this.isSubmitting.set(false);
        this.successMessage.set(`Employé créé (ID ${res.employeeId}). Email d'activation envoyé à ${res.email}.`);
        setTimeout(() => this.router.navigate(
          this.jobId !== null ? ['/dashboard/recruitment/job', this.jobId] : ['/dashboard']
        ), 2000);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.errorMessage.set(err?.error?.message || "Erreur lors de la création de l'employé.");
      }
    });
  }
}
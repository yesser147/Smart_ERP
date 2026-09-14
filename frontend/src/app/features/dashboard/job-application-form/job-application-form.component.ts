import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { JobPostingDTO } from '../../../core/models/hr.model';

@Component({
  selector: 'app-job-application-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './job-application-form.component.html'
})
export class JobApplicationFormComponent implements OnInit {
  private fb = inject(NonNullableFormBuilder);
  private http = inject(HttpClient);
  private route = inject(ActivatedRoute);
  private hrService = inject(HrService);

  private baseUrl = 'http://localhost:8080/api/v1/public/applications';

  jobPostings: JobPostingDTO[] = [];
  selectedFile: File | null = null;
  isSubmitting = false;
  successMessage: string | null = null;
  errorMessage: string | null = null;

  // yearsOfExperience removed on purpose -- it's deduced by the LLM from
  // the actual CV text once "Traiter CV" runs, not asked of the applicant.
  applicationForm = this.fb.group({
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    phoneNumber: [''],
    educationLevel: [''],
    jobId: [null as number | null, Validators.required],
    desiredSalary: [null as number | null],
  });

  ngOnInit(): void {
    this.hrService.getAllJobPostings().subscribe(jobs => {
      this.jobPostings = jobs.filter(j => !j.status || j.status.toUpperCase() === 'OPEN');
    });

    const jobIdParam = this.route.snapshot.queryParamMap.get('jobId');
    if (jobIdParam) this.applicationForm.patchValue({ jobId: Number(jobIdParam) });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
  }

  onSubmit(): void {
    if (this.applicationForm.invalid || !this.selectedFile) {
      this.applicationForm.markAllAsTouched();
      if (!this.selectedFile) this.errorMessage = 'Veuillez joindre votre CV (PDF).';
      return;
    }

    const formValue = this.applicationForm.getRawValue();
    const formData = new FormData();
    Object.entries(formValue).forEach(([key, value]) => {
      if (value !== null && value !== '') formData.append(key, String(value));
    });
    formData.append('cv', this.selectedFile);

    this.isSubmitting = true;
    this.errorMessage = null;
    this.successMessage = null;

    // IMPORTANT: never set a Content-Type header manually here. The
    // browser must set it itself (including the multipart boundary
    // string) when the body is a FormData object. Manually setting
    // Content-Type: multipart/form-data (via an interceptor or an
    // explicit headers object on this call) is what produces a broken
    // request with no boundary -- and in some setups, code that builds
    // the request URL by concatenating strings can end up appending the
    // content-type value onto the URL path itself, which is exactly the
    // ".../applications/multipart/form-data" 404 you saw.
    this.http.post<{ message: string }>(this.baseUrl, formData).subscribe({
      next: (res) => {
        this.isSubmitting = false;
        this.successMessage = res.message;
        this.applicationForm.reset();
        this.selectedFile = null;
      },
      error: (err) => {
        this.isSubmitting = false;
        this.errorMessage = err?.error?.message || "Erreur lors de l'envoi de la candidature.";
      }
    });
  }
}
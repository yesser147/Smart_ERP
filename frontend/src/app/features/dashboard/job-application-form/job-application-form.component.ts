import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';

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

  private baseUrl = 'http://localhost:8080/api/v1/public/applications/multipart/form-data';

  selectedFile: File | null = null;
  isSubmitting = false;
  successMessage: string | null = null;
  errorMessage: string | null = null;

  applicationForm = this.fb.group({
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    phoneNumber: [''],
    educationLevel: [''],
    yearsOfExperience: [null as number | null],
    jobId: [null as number | null, Validators.required],
    desiredSalary: [null as number | null],
  });

  ngOnInit(): void {
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
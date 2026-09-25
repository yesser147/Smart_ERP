import { Component, EventEmitter, Input, OnChanges, Output, inject } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { PublicService } from '../../../core/services/public.service';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

export interface ApplyJobOption {
  jobId: number;
  title: string;
  department?: string | null;
}

const MAX_CV_BYTES = 10 * 1024 * 1024;

/** Application form (name, contact, CV). Used by the public careers page
 *  and by HR to enter an application received by other means. */
@Component({
  selector: 'app-apply-form',
  standalone: true,
  imports: [ReactiveFormsModule, IconComponent],
  templateUrl: './apply-form.component.html'
})
export class ApplyFormComponent implements OnChanges {
  private fb = inject(NonNullableFormBuilder);
  private publicService = inject(PublicService);

  @Input() jobs: ApplyJobOption[] = [];
  @Input() jobId: number | null = null;
  @Input() lockJob = false;
  @Output() submitted = new EventEmitter<string>();

  readonly educationLevels = ['High School', "Associate's", "Bachelor's", "Master's", 'PhD'];

  file: File | null = null;
  fileError: string | null = null;
  submitting = false;
  error: string | null = null;

  form = this.fb.group({
    firstName: ['', [Validators.required, Validators.maxLength(100)]],
    lastName: ['', [Validators.required, Validators.maxLength(100)]],
    email: ['', [Validators.required, Validators.email]],
    phoneNumber: [''],
    educationLevel: [''],
    jobId: [null as number | null, Validators.required],
    desiredSalary: [null as number | null, Validators.min(0)],
  });

  ngOnChanges(): void {
    if (this.jobId !== null) this.form.patchValue({ jobId: this.jobId });
  }

  onFile(event: Event): void {
    const f = (event.target as HTMLInputElement).files?.[0] ?? null;
    this.fileError = null;
    if (f && f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')) {
      this.fileError = 'The CV must be a PDF file.';
      this.file = null;
    } else if (f && f.size > MAX_CV_BYTES) {
      this.fileError = 'The CV must be smaller than 10 MB.';
      this.file = null;
    } else {
      this.file = f;
    }
  }

  invalid(name: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[name];
    return c.invalid && c.touched;
  }

  submit(): void {
    if (this.form.invalid || !this.file) {
      this.form.markAllAsTouched();
      if (!this.file && !this.fileError) this.fileError = 'Attach a CV (PDF).';
      return;
    }
    const data = new FormData();
    Object.entries(this.form.getRawValue()).forEach(([k, v]) => {
      if (v !== null && v !== '') data.append(k, String(v));
    });
    data.append('cv', this.file);

    this.submitting = true;
    this.error = null;
    // no Content-Type header: the browser sets the multipart boundary itself
    this.publicService.apply(data).subscribe({
      next: res => {
        this.submitting = false;
        this.form.reset({ jobId: this.lockJob ? this.jobId : null });
        this.file = null;
        this.submitted.emit(res?.message || 'Application received.');
      },
      error: err => {
        this.submitting = false;
        this.error = err?.status === 429
          ? 'Too many applications from this network. Please try again in a few minutes.'
          : errorMessage(err, 'The application could not be sent.');
      }
    });
  }
}

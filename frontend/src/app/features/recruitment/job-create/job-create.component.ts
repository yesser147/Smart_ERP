import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { AiService } from '../../../core/services/ai.service';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { DepartmentDTO } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

@Component({
  selector: 'app-job-create',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, PageHeaderComponent, IconComponent],
  templateUrl: './job-create.component.html'
})
export class JobCreateComponent implements OnInit {
  private fb = inject(FormBuilder);
  private hr = inject(HrService);
  private ai = inject(AiService);
  private analytics = inject(AnalyticsService);
  private router = inject(Router);

  teams: DepartmentDTO[] = [];
  skills: string[] = [];
  generating = false;
  saving = false;
  aiError: string | null = null;
  saveError: string | null = null;

  form = this.fb.nonNullable.group({
    title: ['', [Validators.required, Validators.maxLength(150)]],
    departmentId: [null as number | null, Validators.required],
    location: [''],
    requiredExperienceYears: [null as number | null, Validators.min(0)],
    offeredSalaryMin: [null as number | null, Validators.min(0)],
    offeredSalaryMax: [null as number | null, Validators.min(0)],
    description: ['', Validators.maxLength(10000)],
  });

  ngOnInit(): void {
    this.hr.getAllDepartments().subscribe(t =>
      this.teams = [...t].sort((a, b) =>
        (a.departmentType ?? '').localeCompare(b.departmentType ?? '') ||
        (a.divisionDescription ?? '').localeCompare(b.divisionDescription ?? '')));
  }

  teamLabel(t: DepartmentDTO): string {
    return `${t.departmentType} · ${t.divisionDescription} (${t.businessUnit})`;
  }

  private selectedTeam(): DepartmentDTO | undefined {
    return this.teams.find(t => t.departmentId === Number(this.form.controls.departmentId.value));
  }

  generate(): void {
    const title = this.form.controls.title.value.trim();
    if (title.length < 2) {
      this.form.controls.title.markAsTouched();
      return;
    }
    this.generating = true;
    this.aiError = null;
    this.ai.generateJobDescription(title, this.selectedTeam()?.departmentType, this.form.controls.requiredExperienceYears.value)
      .subscribe({
        next: res => {
          this.form.controls.description.setValue(res.description);
          this.skills = res.skills ?? [];
          this.generating = false;
        },
        error: err => {
          this.aiError = errorMessage(err, 'The AI could not write the description. Try again or write it yourself.');
          this.generating = false;
        }
      });
  }

  get salaryRangeInvalid(): boolean {
    const { offeredSalaryMin: min, offeredSalaryMax: max } = this.form.getRawValue();
    return min != null && max != null && Number(min) > Number(max);
  }

  submit(): void {
    if (this.form.invalid || this.salaryRangeInvalid) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    this.saving = true;
    this.saveError = null;
    this.hr.createJobPosting({
      title: v.title.trim(),
      departmentId: Number(v.departmentId),
      location: v.location.trim() || null,
      requiredExperienceYears: v.requiredExperienceYears,
      offeredSalaryMin: v.offeredSalaryMin,
      offeredSalaryMax: v.offeredSalaryMax,
      description: v.description.trim() || null,
    }).subscribe({
      next: job => {
        this.analytics.invalidate();
        this.router.navigate(['/dashboard/jobs', job.jobId]);
      },
      error: err => {
        this.saveError = errorMessage(err, 'The job opening could not be created.');
        this.saving = false;
      }
    });
  }

  invalid(name: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[name];
    return c.invalid && c.touched;
  }
}

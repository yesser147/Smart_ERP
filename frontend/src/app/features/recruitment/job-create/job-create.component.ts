import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { AiService } from '../../../core/services/ai.service';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { DepartmentDTO, JobPostingDTO } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

const NEW_TITLE = '__new__';

/** New opening: an existing job title (its skills are reused) or a new one, and a
 *  description always written by the AI, so the text is clean and the skills used to
 *  rank the CVs are the right ones. */
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

  readonly NEW_TITLE = NEW_TITLE;
  teams: DepartmentDTO[] = [];
  /** existing titles -> their latest opening (to prefill the form) */
  titles: { title: string; latest: JobPostingDTO }[] = [];

  description = '';
  skills: string[] = [];
  knownTitle = false;
  /** what the description was written for: if the role changes, it must be written again */
  private writtenFor: string | null = null;

  generating = false;
  saving = false;
  aiError: string | null = null;
  saveError: string | null = null;

  form = this.fb.nonNullable.group({
    titleChoice: ['', Validators.required],
    newTitle: ['', Validators.maxLength(150)],
    departmentId: [null as number | null, Validators.required],
    location: [''],
    requiredExperienceYears: [null as number | null, Validators.min(0)],
    offeredSalaryMin: [null as number | null, Validators.min(0)],
    offeredSalaryMax: [null as number | null, Validators.min(0)],
    notes: ['', Validators.maxLength(1500)],
  });

  ngOnInit(): void {
    this.hr.getAllDepartments().subscribe(t =>
      this.teams = [...t].sort((a, b) =>
        (a.departmentType ?? '').localeCompare(b.departmentType ?? '') ||
        (a.divisionDescription ?? '').localeCompare(b.divisionDescription ?? '')));

    this.hr.getAllJobPostings().subscribe(jobs => {
      const latest = new Map<string, JobPostingDTO>();
      for (const j of jobs) {
        const key = j.title.trim();
        const seen = latest.get(key);
        if (!seen || (j.createdAt ?? '') > (seen.createdAt ?? '')) latest.set(key, j);
      }
      this.titles = [...latest.entries()]
        .map(([title, job]) => ({ title, latest: job }))
        .sort((a, b) => a.title.localeCompare(b.title));
    });

    this.form.controls.titleChoice.valueChanges.subscribe(choice => this.onTitleChoice(choice));
  }

  get isNewTitle(): boolean {
    return this.form.controls.titleChoice.value === NEW_TITLE;
  }

  /** The title that will be published. */
  get title(): string {
    return (this.isNewTitle ? this.form.controls.newTitle.value : this.form.controls.titleChoice.value).trim();
  }

  private onTitleChoice(choice: string): void {
    const known = this.titles.find(t => t.title === choice);
    if (!known) return;
    // reuse the latest opening of this job as a starting point (still editable)
    const j = known.latest;
    this.form.patchValue({
      departmentId: j.departmentId ?? null,
      location: j.location ?? '',
      requiredExperienceYears: j.requiredExperienceYears,
      offeredSalaryMin: j.offeredSalaryMin,
      offeredSalaryMax: j.offeredSalaryMax,
    });
  }

  teamLabel(t: DepartmentDTO): string {
    return `${t.departmentType} · ${t.divisionDescription} (${t.businessUnit})`;
  }

  private selectedTeam(): DepartmentDTO | undefined {
    return this.teams.find(t => t.departmentId === Number(this.form.controls.departmentId.value));
  }

  /** Everything the text depends on. */
  private roleKey(): string {
    const v = this.form.getRawValue();
    return JSON.stringify([this.title.toLowerCase(), v.departmentId, v.requiredExperienceYears, v.notes.trim()]);
  }

  get titleMissing(): boolean {
    return this.title.length < 2;
  }

  get stale(): boolean {
    return !!this.description && this.writtenFor !== this.roleKey();
  }

  get canPublish(): boolean {
    return !!this.description && !this.stale && !this.generating;
  }

  generate(): void {
    this.form.controls.titleChoice.markAsTouched();
    this.form.controls.newTitle.markAsTouched();
    this.form.controls.departmentId.markAsTouched();
    if (this.titleMissing || this.form.controls.departmentId.invalid) return;

    const team = this.selectedTeam();
    const key = this.roleKey();
    this.generating = true;
    this.aiError = null;
    this.ai.generateJobDescription({
      title: this.title,
      department: team?.departmentType,
      team: team?.divisionDescription,
      requiredExperienceYears: this.form.controls.requiredExperienceYears.value,
      notes: this.form.controls.notes.value.trim(),
    }).subscribe({
      next: res => {
        this.description = res.description;
        this.skills = res.skills ?? [];
        this.knownTitle = res.known_title;
        this.writtenFor = key;
        this.generating = false;
      },
      error: err => {
        this.aiError = errorMessage(err, 'The AI could not write the description. Check that the AI engine is running and try again.');
        this.generating = false;
      }
    });
  }

  get salaryRangeInvalid(): boolean {
    const { offeredSalaryMin: min, offeredSalaryMax: max } = this.form.getRawValue();
    return min != null && max != null && Number(min) > Number(max);
  }

  submit(): void {
    if (this.form.invalid || this.titleMissing || this.salaryRangeInvalid || !this.canPublish) {
      this.form.markAllAsTouched();
      if (!this.description) this.aiError = 'Write the description with the AI before publishing.';
      return;
    }
    const v = this.form.getRawValue();
    this.saving = true;
    this.saveError = null;
    this.hr.createJobPosting({
      title: this.title,
      departmentId: Number(v.departmentId),
      location: v.location.trim() || null,
      requiredExperienceYears: v.requiredExperienceYears,
      offeredSalaryMin: v.offeredSalaryMin,
      offeredSalaryMax: v.offeredSalaryMax,
      description: this.description,
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

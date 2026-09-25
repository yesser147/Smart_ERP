import { Component, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { PublicService } from '../../core/services/public.service';
import { PublicJobDTO } from '../../core/models/hr.model';
import { IconComponent } from '../../shared/components/icon/icon.component';
import { ApplyFormComponent, ApplyJobOption } from './apply-form/apply-form.component';

/** Public job board: no login. */
@Component({
  selector: 'app-careers',
  standalone: true,
  imports: [DatePipe, FormsModule, RouterLink, IconComponent, ApplyFormComponent],
  templateUrl: './careers.component.html'
})
export class CareersComponent implements OnInit {
  private publicService = inject(PublicService);

  jobs: PublicJobDTO[] = [];
  loading = true;
  error = false;

  search = '';
  department = '';
  selected: PublicJobDTO | null = null;
  applying = false;
  confirmation: string | null = null;

  ngOnInit(): void {
    this.publicService.openJobs().subscribe({
      next: jobs => { this.jobs = jobs; this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  get departments(): string[] {
    return [...new Set(this.jobs.map(j => j.department).filter((d): d is string => !!d))].sort();
  }

  get filtered(): PublicJobDTO[] {
    const q = this.search.trim().toLowerCase();
    return this.jobs
      .filter(j => !this.department || j.department === this.department)
      .filter(j => !q || `${j.title} ${j.location} ${j.department}`.toLowerCase().includes(q));
  }

  get options(): ApplyJobOption[] {
    return this.selected ? [{ jobId: this.selected.jobId, title: this.selected.title, department: this.selected.department }] : [];
  }

  open(job: PublicJobDTO): void {
    this.selected = job;
    this.applying = false;
    this.confirmation = null;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  close(): void {
    this.selected = null;
    this.applying = false;
    this.confirmation = null;
  }

  salary(j: PublicJobDTO): string | null {
    if (j.salaryMin == null && j.salaryMax == null) return null;
    const k = (v: number | null) => (v == null ? '?' : `$${Math.round(v / 1000)}k`);
    return `${k(j.salaryMin)} – ${k(j.salaryMax)}`;
  }
}

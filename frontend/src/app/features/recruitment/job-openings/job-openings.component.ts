import { Component, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { JobPostingDTO } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

const PAGE_SIZE = 15;

@Component({
  selector: 'app-job-openings',
  standalone: true,
  imports: [DatePipe, FormsModule, RouterLink, PageHeaderComponent, StatusBadgeComponent, IconComponent],
  templateUrl: './job-openings.component.html'
})
export class JobOpeningsComponent implements OnInit {
  private hr = inject(HrService);

  jobs: JobPostingDTO[] = [];
  loading = true;
  error = false;

  search = '';
  department = '';
  status: 'OPEN' | 'CLOSED' | 'FILLED' | '' = 'OPEN';
  page = 1;

  ngOnInit(): void {
    this.hr.getAllJobPostings().subscribe({
      next: jobs => { this.jobs = jobs; this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  get departments(): string[] {
    return [...new Set(this.jobs.map(j => j.departmentType || 'Unassigned'))].sort();
  }

  count(status: string): number {
    return this.jobs.filter(j => (j.status ?? 'OPEN').toUpperCase() === status).length;
  }

  get filtered(): JobPostingDTO[] {
    const q = this.search.trim().toLowerCase();
    return this.jobs
      .filter(j => !this.status || (j.status ?? 'OPEN').toUpperCase() === this.status)
      .filter(j => !this.department || (j.departmentType || 'Unassigned') === this.department)
      .filter(j => !q || `${j.title} ${j.divisionDescription} ${j.location}`.toLowerCase().includes(q))
      .sort((a, b) => (b.createdAt ?? '').localeCompare(a.createdAt ?? '') || b.jobId - a.jobId);
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filtered.length / PAGE_SIZE));
  }

  get pageJobs(): JobPostingDTO[] {
    return this.filtered.slice((this.page - 1) * PAGE_SIZE, this.page * PAGE_SIZE);
  }

  setStatus(s: 'OPEN' | 'CLOSED' | 'FILLED' | ''): void {
    this.status = s;
    this.page = 1;
  }

  resetPage(): void {
    this.page = 1;
  }

  goTo(p: number): void {
    this.page = Math.min(Math.max(1, p), this.totalPages);
  }

  salary(j: JobPostingDTO): string {
    if (j.offeredSalaryMin == null && j.offeredSalaryMax == null) return '—';
    const k = (v: number | null) => (v == null ? '?' : `${Math.round(v / 1000)}k`);
    return `$${k(j.offeredSalaryMin)} – ${k(j.offeredSalaryMax)}`;
  }
}

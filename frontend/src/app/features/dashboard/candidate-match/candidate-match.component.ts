import { Component, Input, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NavigationEnd, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { HrService } from '../../../core/services/hr.service';
import { JobPostingDTO } from '../../../core/models/hr.model';

const PAGE_SIZE = 15;

@Component({
  selector: 'app-candidate-match',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './candidate-match.component.html'
})
export class CandidateMatchComponent implements OnChanges {
  private hrService = inject(HrService);
  private router = inject(Router);

  @Input() jobPostings: JobPostingDTO[] = [];

  search = '';
  departmentFilter = '';
  showFilled = false;                 // filled postings hidden by default

  departments: string[] = [];
  filtered: JobPostingDTO[] = [];
  pageJobs: JobPostingDTO[] = [];
  page = 1;
  totalPages = 1;

  private applicantCounts = new Map<number, number>();
  private titleTotals = new Map<string, number>();
  private titleOpen = new Map<string, number>();

  constructor() {
    // back on the dashboard (e.g. after a hire) -> refresh statuses and counts
    this.router.events
      .pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        filter(e => e.urlAfterRedirects.split('?')[0] === '/dashboard'),
        takeUntilDestroyed()
      )
      .subscribe(() => this.reload());
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['jobPostings']) {
      this.rebuild();
      this.loadApplicantCounts();
    }
  }

  private reload(): void {
    this.hrService.getAllJobPostings().subscribe(jobs => {
      this.jobPostings = jobs;
      this.rebuild();
    });
    this.loadApplicantCounts();
  }

  private loadApplicantCounts(): void {
    this.hrService.getAllJobApplications().subscribe(apps => {
      this.applicantCounts.clear();
      for (const a of apps) {
        if (a.jobId == null) continue;
        this.applicantCounts.set(a.jobId, (this.applicantCounts.get(a.jobId) ?? 0) + 1);
      }
    });
  }

  private deptOf(j: JobPostingDTO): string {
    return j.departmentType || j.businessUnit || 'Unassigned';
  }

  private isOpen(j: JobPostingDTO): boolean {
    return !j.status || j.status.toUpperCase() === 'OPEN';
  }

  private titleKey(j: JobPostingDTO): string {
    return `${this.deptOf(j)}||${(j.title ?? '').trim().toLowerCase()}`;
  }

  /** Recomputes counts, filters, sorting and the current page. Called on change, never from the template. */
  private rebuild(): void {
    this.titleTotals.clear();
    this.titleOpen.clear();
    for (const j of this.jobPostings) {
      const k = this.titleKey(j);
      this.titleTotals.set(k, (this.titleTotals.get(k) ?? 0) + 1);
      if (this.isOpen(j)) this.titleOpen.set(k, (this.titleOpen.get(k) ?? 0) + 1);
    }

    const visible = this.jobPostings.filter(j => this.showFilled || this.isOpen(j));
    this.departments = [...new Set(visible.map(j => this.deptOf(j)))].sort();

    const q = this.search.trim().toLowerCase();
    this.filtered = visible
      .filter(j => !this.departmentFilter || this.deptOf(j) === this.departmentFilter)
      .filter(j => !q || (j.title ?? '').toLowerCase().includes(q))
      .sort((a, b) =>
        this.deptOf(a).localeCompare(this.deptOf(b)) ||
        (a.title ?? '').localeCompare(b.title ?? '') ||
        (a.jobId ?? 0) - (b.jobId ?? 0));

    this.totalPages = Math.max(1, Math.ceil(this.filtered.length / PAGE_SIZE));
    this.page = Math.min(this.page, this.totalPages);
    this.pageJobs = this.filtered.slice((this.page - 1) * PAGE_SIZE, this.page * PAGE_SIZE);
  }

  onFilterChange(): void {
    this.page = 1;
    this.rebuild();
  }

  onShowFilledChange(): void {
    this.rebuild();
    if (this.departmentFilter && !this.departments.includes(this.departmentFilter)) {
      this.departmentFilter = '';
    }
    this.onFilterChange();
  }

  goToPage(p: number): void {
    this.page = Math.min(Math.max(1, p), this.totalPages);
    this.rebuild();
  }

  // ---- template helpers ----

  deptLabel(j: JobPostingDTO): string {
    return [this.deptOf(j), j.divisionDescription].filter(Boolean).join(' · ');
  }

  applicantsOf(j: JobPostingDTO): number {
    return this.applicantCounts.get(j.jobId as number) ?? 0;
  }

  totalInTitle(j: JobPostingDTO): number {
    return this.titleTotals.get(this.titleKey(j)) ?? 1;
  }

  openInTitle(j: JobPostingDTO): number {
    return this.titleOpen.get(this.titleKey(j)) ?? 0;
  }

  isDuplicate(j: JobPostingDTO): boolean {
    return this.totalInTitle(j) > 1;
  }

  statusClass(status: string | undefined): string {
    switch ((status ?? 'OPEN').toUpperCase()) {
      case 'OPEN': return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'FILLED': return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'CLOSED': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  }

  openJob(j: JobPostingDTO): void {
    if (j.jobId == null) return;
    this.router.navigate(['/dashboard/recruitment/job', j.jobId]);
  }
}
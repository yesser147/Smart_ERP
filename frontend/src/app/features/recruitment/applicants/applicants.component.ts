import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subscription, catchError, concatMap, from, of, tap } from 'rxjs';

import { AiService } from '../../../core/services/ai.service';
import { HrService } from '../../../core/services/hr.service';
import { ApplicantWithCvStatus } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

type CvFilter = '' | 'pending' | 'analysed' | 'none';
const PAGE_SIZE = 20;

@Component({
  selector: 'app-applicants',
  standalone: true,
  imports: [DatePipe, FormsModule, RouterLink, PageHeaderComponent, IconComponent],
  templateUrl: './applicants.component.html'
})
export class ApplicantsComponent implements OnInit {
  private hr = inject(HrService);
  private ai = inject(AiService);
  private destroyRef = inject(DestroyRef);

  applicants: ApplicantWithCvStatus[] = [];
  loading = true;
  error = false;

  search = '';
  cvFilter: CvFilter = '';
  sort: 'createdAt' | 'name' = 'createdAt';
  sortDesc = true;
  page = 1;

  /** Per-row analysis state (single or batch). */
  busy = new Set<number>();
  errors = new Map<number, string>();
  batch: Subscription | null = null;
  batchDone = 0;
  batchTotal = 0;

  ngOnInit(): void {
    this.load();
    this.destroyRef.onDestroy(() => this.batch?.unsubscribe());
  }

  load(): void {
    this.loading = true;
    this.error = false;
    this.hr.getApplicantsWithCvStatus().subscribe({
      next: data => { this.applicants = data; this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  count(f: CvFilter): number {
    return this.applicants.filter(a => this.matches(a, f)).length;
  }

  private matches(a: ApplicantWithCvStatus, f: CvFilter): boolean {
    switch (f) {
      case 'pending': return a.hasCv && !a.isProcessed;
      case 'analysed': return a.isProcessed;
      case 'none': return !a.hasCv;
      default: return true;
    }
  }

  get filtered(): ApplicantWithCvStatus[] {
    const q = this.search.trim().toLowerCase();
    const dir = this.sortDesc ? -1 : 1;
    return this.applicants
      .filter(a => this.matches(a, this.cvFilter))
      .filter(a => !q || `${a.firstName} ${a.lastName} ${a.email}`.toLowerCase().includes(q))
      .sort((a, b) => this.sort === 'name'
        ? dir * `${a.lastName} ${a.firstName}`.localeCompare(`${b.lastName} ${b.firstName}`)
        : dir * (new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()));
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filtered.length / PAGE_SIZE));
  }

  get pageRows(): ApplicantWithCvStatus[] {
    return this.filtered.slice((this.page - 1) * PAGE_SIZE, this.page * PAGE_SIZE);
  }

  setFilter(f: CvFilter): void {
    this.cvFilter = f;
    this.page = 1;
  }

  toggleSort(col: 'createdAt' | 'name'): void {
    if (this.sort === col) this.sortDesc = !this.sortDesc;
    else { this.sort = col; this.sortDesc = col === 'createdAt'; }
    this.page = 1;
  }

  resetPage(): void {
    this.page = 1;
  }

  goTo(p: number): void {
    this.page = Math.min(Math.max(1, p), this.totalPages);
  }

  private analyse$(a: ApplicantWithCvStatus) {
    this.busy.add(a.applicantId);
    this.errors.delete(a.applicantId);
    return this.ai.processCv(a.applicantId).pipe(
      tap(() => a.isProcessed = true),
      catchError(err => {
        this.errors.set(a.applicantId, errorMessage(err, 'The CV could not be analysed.'));
        return of(null);
      }),
      tap(() => this.busy.delete(a.applicantId))
    );
  }

  analyse(a: ApplicantWithCvStatus): void {
    this.analyse$(a).subscribe();
  }

  /** Every CV not analysed yet, one at a time (each one is an LLM call). */
  analyseAllPending(): void {
    const pending = this.applicants.filter(a => a.hasCv && !a.isProcessed);
    if (!pending.length) return;
    this.batchDone = 0;
    this.batchTotal = pending.length;
    this.batch = from(pending).pipe(
      concatMap(a => this.analyse$(a)),
      tap(() => this.batchDone++)
    ).subscribe({ complete: () => this.batch = null });
  }

  stopBatch(): void {
    this.batch?.unsubscribe();
    this.batch = null;
    this.busy.clear();
  }
}

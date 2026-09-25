import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subscription, catchError, concatMap, from, of, tap } from 'rxjs';

import { AiService } from '../../../core/services/ai.service';
import { HrService } from '../../../core/services/hr.service';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { JobApplicationDTO, JobPostingDTO } from '../../../core/models/hr.model';
import { CandidateMatch, JobMatchResult } from '../../../core/models/ai.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

const STEP = 10;

const CAN_INTERVIEW = ['APPLIED', 'IN REVIEW'];
const CAN_OFFER = ['APPLIED', 'IN REVIEW', 'INTERVIEWING'];
const CAN_REJECT = ['APPLIED', 'IN REVIEW', 'INTERVIEWING'];

@Component({
  selector: 'app-job-candidates',
  standalone: true,
  imports: [DatePipe, NgClass, RouterLink, PageHeaderComponent, StatusBadgeComponent, IconComponent],
  templateUrl: './job-candidates.component.html'
})
export class JobCandidatesComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private ai = inject(AiService);
  private hr = inject(HrService);
  private analytics = inject(AnalyticsService);
  private destroyRef = inject(DestroyRef);

  jobId!: number;

  // --- the posting (backend): always shown, even when the AI engine is down
  job: JobPostingDTO | null = null;
  jobState: 'loading' | 'ready' | 'missing' = 'loading';
  showDescription = false;
  statusBusy = false;

  // --- applications (backend)
  applications = new Map<number, JobApplicationDTO>();
  actionBusy: number | null = null;
  actionError: string | null = null;

  // --- AI ranking
  topK = STEP;
  matchLoading = true;
  matchError: string | null = null;
  match: JobMatchResult | null = null;
  requiredSkills: string[] = [];
  private matchSeq = 0;

  // --- batch CV processing
  processing = false;
  processed = 0;
  processTotal = 0;
  processFailures: { applicantId: number; name: string; reason: string }[] = [];
  private processSub?: Subscription;

  ngOnInit(): void {
    this.jobId = Number(this.route.snapshot.paramMap.get('jobId'));
    this.loadJob();
    this.loadApplications();
    this.runMatch();
    this.destroyRef.onDestroy(() => this.processSub?.unsubscribe());
  }

  // ------------------------------------------------------------------ posting

  private loadJob(): void {
    this.hr.getJobPosting(this.jobId).subscribe({
      next: job => { this.job = job; this.jobState = 'ready'; },
      error: () => this.jobState = 'missing'
    });
  }

  setStatus(status: 'OPEN' | 'CLOSED' | 'FILLED'): void {
    this.statusBusy = true;
    this.hr.setJobPostingStatus(this.jobId, status).subscribe({
      next: job => {
        this.job = job;
        this.statusBusy = false;
        this.analytics.invalidate();
      },
      error: err => {
        this.actionError = errorMessage(err, 'The status could not be changed.');
        this.statusBusy = false;
      }
    });
  }

  get salaryRange(): string {
    const j = this.job;
    if (!j || (j.offeredSalaryMin == null && j.offeredSalaryMax == null)) return '—';
    const f = (v: number | null) => (v == null ? '?' : `$${Math.round(v).toLocaleString('en-US')}`);
    return `${f(j.offeredSalaryMin)} – ${f(j.offeredSalaryMax)}`;
  }

  // ------------------------------------------------------------------ applications

  private loadApplications(): void {
    this.hr.getApplicationsForJob(this.jobId).subscribe({
      next: apps => {
        this.applications.clear();
        apps.forEach(a => this.applications.set(a.applicantId, a));
      }
    });
  }

  applicationFor(applicantId: number): JobApplicationDTO | undefined {
    return this.applications.get(applicantId);
  }

  /** Applicants whose CV has not been analysed yet (not ranked by the AI). */
  get waiting(): JobApplicationDTO[] {
    const ids = new Set(this.match?.unprocessed_applicant_ids ?? []);
    return [...this.applications.values()].filter(a => ids.has(a.applicantId));
  }

  can(action: 'interview' | 'offer' | 'reject' | 'hire', app: JobApplicationDTO): boolean {
    const s = (app.status ?? '').toUpperCase();
    switch (action) {
      case 'interview': return CAN_INTERVIEW.includes(s);
      case 'offer': return CAN_OFFER.includes(s);
      case 'reject': return CAN_REJECT.includes(s);
      case 'hire': return s === 'OFFERED' && this.job?.status !== 'FILLED';
    }
  }

  act(action: 'interview' | 'offer' | 'reject', app: JobApplicationDTO): void {
    this.actionBusy = app.applicantId;
    this.actionError = null;
    const call = action === 'interview' ? this.hr.moveToInterview(app.applicationId)
      : action === 'offer' ? this.hr.moveToOffered(app.applicationId)
      : this.hr.rejectApplication(app.applicationId);
    call.subscribe({
      next: updated => {
        this.applications.set(updated.applicantId, updated);
        this.actionBusy = null;
        this.analytics.invalidate();
      },
      error: err => {
        this.actionError = errorMessage(err, 'The action failed.');
        this.actionBusy = null;
      }
    });
  }

  hire(app: JobApplicationDTO): void {
    this.router.navigate(['/dashboard/applicant', app.applicantId, 'hire'], {
      queryParams: { jobApplicationId: app.applicationId, jobId: this.jobId }
    });
  }

  // ------------------------------------------------------------------ AI ranking

  runMatch(recomputeAll = false): void {
    const seq = ++this.matchSeq;
    this.matchLoading = true;
    this.matchError = null;
    this.ai.matchCandidates(this.jobId, this.topK, recomputeAll).subscribe({
      next: res => {
        if (seq !== this.matchSeq) return;
        this.match = res;
        this.requiredSkills = (res.required_skills ?? '').split(',').map(s => s.trim()).filter(Boolean);
        this.matchLoading = false;
      },
      error: err => {
        if (seq !== this.matchSeq) return;
        this.matchError = errorMessage(err, 'The AI engine did not answer.');
        this.matchLoading = false;
      }
    });
  }

  get candidates(): CandidateMatch[] {
    return this.match?.candidates ?? [];
  }

  get canShowMore(): boolean {
    return !this.matchLoading && !!this.match
      && this.candidates.length >= this.topK && this.candidates.length < this.match.n_processed;
  }

  showMore(): void {
    this.topK += STEP;
    this.runMatch();
  }

  parseSkills(json: string): string[] {
    try { return JSON.parse(json) ?? []; } catch { return []; }
  }

  scoreRing(score: number): string {
    if (score >= 75) return 'text-emerald-300 ring-emerald-500/30 bg-emerald-500/10';
    if (score >= 50) return 'text-amber-300 ring-amber-500/30 bg-amber-500/10';
    return 'text-slate-300 ring-slate-500/30 bg-slate-500/10';
  }

  // ------------------------------------------------------------------ batch CV analysis

  /** Analyses the unprocessed CVs one by one (each is an LLM call), then re-ranks. */
  processRemaining(): void {
    const ids = [...(this.match?.unprocessed_applicant_ids ?? [])];
    if (!ids.length) return;
    this.processing = true;
    this.processed = 0;
    this.processTotal = ids.length;
    this.processFailures = [];

    this.processSub = from(ids).pipe(
      concatMap(id => this.ai.processCv(id).pipe(
        catchError(err => {
          const app = this.applications.get(id);
          this.processFailures.push({ applicantId: id, name: app?.applicantName ?? `#${id}`, reason: errorMessage(err, 'failed') });
          return of(null);
        }),
        tap(() => this.processed++)
      ))
    ).subscribe({
      complete: () => {
        this.processing = false;
        this.runMatch();
      }
    });
  }

  stopProcessing(): void {
    this.processSub?.unsubscribe();
    this.processing = false;
    this.runMatch();
  }

  get processPct(): number {
    return this.processTotal ? Math.round((this.processed / this.processTotal) * 100) : 0;
  }
}

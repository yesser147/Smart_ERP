import { Component, Input, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { AiService } from '../../../core/services/ai.service';
import { HrService } from '../../../core/services/hr.service';
import { JobPostingDTO, JobApplicationDTO } from '../../../core/models/hr.model';
import { CandidateMatch } from '../../../core/models/ai.model';

@Component({
  selector: 'app-candidate-match',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './candidate-match.component.html'
})
export class CandidateMatchComponent implements OnChanges {
  private aiService = inject(AiService);
  private hrService = inject(HrService);
  private router = inject(Router);

  @Input() jobPostings: JobPostingDTO[] = [];

  selectedJobId: number | null = null;
  loading = false;
  error = false;
  jobTitle = '';
  candidates: CandidateMatch[] = [];
  processingId: number | null = null;

  applicationsByApplicantId = new Map<number, JobApplicationDTO>();
  actioningApplicantId: number | null = null;
  private requestSeq = 0;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['jobPostings'] && this.jobPostings.length > 0 && this.selectedJobId === null) {
      const firstOpen = this.jobPostings.find(j => !j.status || j.status.toUpperCase() === 'OPEN');
      this.selectedJobId = firstOpen ? (firstOpen as any).jobId ?? (firstOpen as any).job_id : null;
      if (this.selectedJobId !== null) this.runMatch();
    }
  }

  parseSkills(skillsJson: string): string[] {
    try {
      return JSON.parse(skillsJson);
    } catch {
      return [];
    }
  }

  scoreClass(score: number): string {
    if (score >= 75) return 'text-teal-400';
    if (score >= 50) return 'text-amber-400';
    return 'text-slate-400';
  }

  /**
   * recomputeAll=false (default, "Rechercher"): reuses cached
   * ai_match_score for every applicant who already has one, and only
   * runs embedding+LLM scoring for applicants who don't (a brand-new
   * application, or a CV just processed by "Traiter CV"). No wasted
   * LLM calls on people already scored.
   *
   * recomputeAll=true ("Recalculer"): forces every real applicant of
   * this job to be rescored from scratch -- use when the job's
   * requirements changed and old scores should be discarded.
   */
  runMatch(recomputeAll: boolean = false): void {
    if (this.selectedJobId === null) return;
    this.selectedJobId = Number(this.selectedJobId);

    const jobId = this.selectedJobId;
    const mySeq = ++this.requestSeq;

    this.loading = true;
    this.error = false;

    forkJoin({
      match: this.aiService.matchCandidates(jobId, 10, recomputeAll),
      apps: this.hrService.getAllJobApplications()
    }).subscribe({
      next: ({ match, apps }) => {
        if (mySeq !== this.requestSeq) return;

        this.jobTitle = match.job_title;
        this.candidates = match.candidates;

        this.applicationsByApplicantId.clear();
        apps
          .filter(a => a.jobId === jobId)
          .forEach(a => this.applicationsByApplicantId.set(a.applicantId, a));

        this.loading = false;
      },
      error: () => {
        if (mySeq !== this.requestSeq) return;
        this.error = true;
        this.loading = false;
      }
    });
  }

  applicationFor(applicantId: number): JobApplicationDTO | undefined {
    return this.applicationsByApplicantId.get(applicantId);
  }

  statusClass(status: string | undefined): string {
    switch (status?.toUpperCase()) {
      case 'APPLIED': return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'IN REVIEW': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'INTERVIEWING': return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
      case 'OFFERED': return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'REJECTED': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  }

  private updateApplication(updated: JobApplicationDTO): void {
    this.applicationsByApplicantId.set(updated.applicantId, updated);
  }

  interview(applicantId: number): void {
    const app = this.applicationsByApplicantId.get(applicantId);
    if (!app) return;
    this.actioningApplicantId = applicantId;
    this.hrService.moveToInterview(app.applicationId).subscribe({
      next: (updated) => { this.updateApplication(updated); this.actioningApplicantId = null; },
      error: () => { this.actioningApplicantId = null; }
    });
  }

  /** "Offre" now means "hire this person": instead of firing an email
   * immediately, it hands off to a form where HR fills in department,
   * salary, title, etc. The application is marked OFFERED when that
   * form is submitted, not on this click. */
  goToHire(applicantId: number): void {
    const app = this.applicationsByApplicantId.get(applicantId);
    this.router.navigate(['/recruitment/hire', applicantId], {
      queryParams: {
        jobApplicationId: app?.applicationId ?? null,
        jobId: this.selectedJobId
      }
    });
  }

  reject(applicantId: number): void {
    const app = this.applicationsByApplicantId.get(applicantId);
    if (!app) return;
    this.actioningApplicantId = applicantId;
    this.hrService.rejectApplication(app.applicationId).subscribe({
      next: (updated) => { this.updateApplication(updated); this.actioningApplicantId = null; },
      error: () => { this.actioningApplicantId = null; }
    });
  }

  processCv(applicantId: number): void {
    this.processingId = applicantId;
    this.aiService.processCv(applicantId).subscribe({
      next: () => { this.processingId = null; /* optionally toast success */ },
      error: () => { this.processingId = null; }
    });
  }
}
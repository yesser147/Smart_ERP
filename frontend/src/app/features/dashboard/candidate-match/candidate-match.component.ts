import { Component, Input, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiService, CandidateMatch } from '../../../core/services/ai.service';
import { HrService } from '../../../core/services/hr.service';
import { JobPostingDTO, JobApplicationDTO } from '../../../core/models/hr.model';

@Component({
  selector: 'app-candidate-match',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './candidate-match.component.html'
})
export class CandidateMatchComponent implements OnChanges {
  private aiService = inject(AiService);
  private hrService = inject(HrService);

  @Input() jobPostings: JobPostingDTO[] = [];

  selectedJobId: number | null = null;
  loading = false;
  error = false;
  jobTitle = '';
  candidates: CandidateMatch[] = [];

  // application_id keyed by applicant_id, for the currently selected job
  // only -- lets each candidate card know whether it has a real
  // application to act on, and which one.
  applicationsByApplicantId = new Map<number, JobApplicationDTO>();
  actioningApplicantId: number | null = null;

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

runMatch(): void {
  if (this.selectedJobId === null) return;
  
  // Ensure the ID is always a number
  this.selectedJobId = Number(this.selectedJobId);
  
  this.loading = true;
  this.error = false;
  this.applicationsByApplicantId.clear();

  this.aiService.matchCandidates(this.selectedJobId, 10).subscribe({
    next: (res) => {
      this.jobTitle = res.job_title;
      this.candidates = res.candidates;
      this.loading = false;
      this.loadApplicationsForJob();
    },
    error: () => {
      this.error = true;
      this.loading = false;
    }
  });
}

  /** Cross-references matched candidates against real applications for
   * this job, so buttons only appear for applicants who actually
   * applied -- a high embedding match score alone doesn't mean they're
   * in the pipeline. */
  private loadApplicationsForJob(): void {
    if (this.selectedJobId === null) return;
    this.hrService.getAllJobApplications().subscribe({
      next: (apps) => {
        this.applicationsByApplicantId.clear();
        apps
          .filter(a => a.jobId === this.selectedJobId)
          .forEach(a => this.applicationsByApplicantId.set(a.applicantId, a));
      },
      error: () => { /* leave buttons hidden if this fails -- non-critical */ }
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

  offer(applicantId: number): void {
    const app = this.applicationsByApplicantId.get(applicantId);
    if (!app) return;
    this.actioningApplicantId = applicantId;
    this.hrService.moveToOffered(app.applicationId).subscribe({
      next: (updated) => { this.updateApplication(updated); this.actioningApplicantId = null; },
      error: () => { this.actioningApplicantId = null; }
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
}
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { AiService } from '../../../core/services/ai.service';
import { HrService } from '../../../core/services/hr.service';
import { JobPostingDTO, JobApplicationDTO } from '../../../core/models/hr.model';
import { CandidateMatch } from '../../../core/models/ai.model';

const STEP = 10;

@Component({
  selector: 'app-job-candidates',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './job-candidates.component.html'
})
export class JobCandidatesComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private aiService = inject(AiService);
  private hrService = inject(HrService);

  jobId!: number;
  job: JobPostingDTO | null = null;
  jobMissing = false;
  titleOpen = 0;
  titleTotal = 0;
  applicantsTotal = 0;

  requiredSkills: string[] = [];
  requiredYears: number | null = null;

  topK = STEP;
  loading = true;
  error = false;
  candidates: CandidateMatch[] = [];

  applicationsByApplicantId = new Map<number, JobApplicationDTO>();
  actioningApplicantId: number | null = null;
  private requestSeq = 0;

  ngOnInit(): void {
    this.jobId = Number(this.route.snapshot.paramMap.get('jobId'));

    this.hrService.getAllJobPostings().subscribe({
      next: (jobs) => {
        const job = jobs.find(j => j.jobId === this.jobId) ?? null;
        this.job = job;
        this.jobMissing = !job;
        if (job) {
          const key = this.titleKey(job);
          const same = jobs.filter(j => this.titleKey(j) === key);
          this.titleTotal = same.length;
          this.titleOpen = same.filter(j => this.isOpen(j)).length;
        }
      },
      error: () => { this.jobMissing = true; }
    });

    this.runMatch();
  }

  // ---------- job helpers ----------

  private deptOf(j: JobPostingDTO): string {
    return j.departmentType || j.businessUnit || 'Unassigned';
  }

  private isOpen(j: JobPostingDTO): boolean {
    return !j.status || j.status.toUpperCase() === 'OPEN';
  }

  private titleKey(j: JobPostingDTO): string {
    return `${this.deptOf(j)}||${(j.title ?? '').trim().toLowerCase()}`;
  }

  deptLabel(j: JobPostingDTO): string {
    return [this.deptOf(j), j.divisionDescription].filter(Boolean).join(' · ');
  }

  // ---------- matching ----------

  runMatch(recomputeAll: boolean = false): void {
    const mySeq = ++this.requestSeq;
    this.loading = true;
    this.error = false;

    forkJoin({
      match: this.aiService.matchCandidates(this.jobId, this.topK, recomputeAll),
      apps: this.hrService.getAllJobApplications()
    }).subscribe({
      next: ({ match, apps }) => {
        if (mySeq !== this.requestSeq) return;

        this.candidates = match.candidates;
        this.requiredSkills = (match.required_skills ?? '')
          .split(',').map(s => s.trim()).filter(Boolean);
        this.requiredYears = match.required_experience_years ?? null;

        this.applicationsByApplicantId.clear();
        const forJob = apps.filter(a => a.jobId === this.jobId);
        this.applicantsTotal = forJob.length;
        forJob.forEach(a => this.applicationsByApplicantId.set(a.applicantId, a));

        this.loading = false;
      },
      error: () => {
        if (mySeq !== this.requestSeq) return;
        this.error = true;
        this.loading = false;
      }
    });
  }

  get canShowMore(): boolean {
    return !this.loading && this.candidates.length >= this.topK
      && this.candidates.length < this.applicantsTotal;
  }

  showMore(): void {
    this.topK += STEP;
    this.runMatch();
  }

  // ---------- candidate list helpers ----------

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

  statusClass(status: string | undefined): string {
    switch (status?.toUpperCase()) {
      case 'OPEN': return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'FILLED': return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'CLOSED': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'APPLIED': return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'IN REVIEW': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'INTERVIEWING': return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
      case 'OFFERED': return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'REJECTED': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  }

  applicationFor(applicantId: number): JobApplicationDTO | undefined {
    return this.applicationsByApplicantId.get(applicantId);
  }

  private updateApplication(updated: JobApplicationDTO): void {
    this.applicationsByApplicantId.set(updated.applicantId, updated);
  }

  // ---------- actions ----------

  interview(applicantId: number): void {
    const app = this.applicationsByApplicantId.get(applicantId);
    if (!app) return;
    this.actioningApplicantId = applicantId;
    this.hrService.moveToInterview(app.applicationId).subscribe({
      next: (updated) => { this.updateApplication(updated); this.actioningApplicantId = null; },
      error: () => { this.actioningApplicantId = null; }
    });
  }

  goToHire(applicantId: number): void {
    const app = this.applicationsByApplicantId.get(applicantId);
    this.router.navigate(['/dashboard/recruitment/hire', applicantId], {
      queryParams: { jobApplicationId: app?.applicationId ?? null, jobId: this.jobId }
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

  goToDetail(applicantId: number): void {
    this.router.navigate(['/dashboard/applicant', applicantId], {
      queryParams: { jobId: this.jobId }
    });
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }
}
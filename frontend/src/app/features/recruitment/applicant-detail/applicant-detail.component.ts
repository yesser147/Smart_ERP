import { Component, ElementRef, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { HrService } from '../../../core/services/hr.service';
import { AiService } from '../../../core/services/ai.service';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { ApplicantDTO, JobApplicationDTO, JobPostingDTO, StatusHistoryDTO } from '../../../core/models/hr.model';
import { ChatMessage, InterviewQuestions } from '../../../core/models/ai.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { errorMessage } from '../../../shared/utils/errors';

const CAN_INTERVIEW = ['APPLIED', 'IN REVIEW'];
const CAN_OFFER = ['APPLIED', 'IN REVIEW', 'INTERVIEWING'];
const CAN_REJECT = ['APPLIED', 'IN REVIEW', 'INTERVIEWING'];

@Component({
  selector: 'app-applicant-detail',
  standalone: true,
  imports: [DatePipe, NgClass, FormsModule, PageHeaderComponent, StatusBadgeComponent, IconComponent, MarkdownPipe],
  templateUrl: './applicant-detail.component.html'
})
export class ApplicantDetailComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private hr = inject(HrService);
  private ai = inject(AiService);
  private analytics = inject(AnalyticsService);

  @ViewChild('chatScroll') chatScroll?: ElementRef<HTMLElement>;

  applicantId!: number;
  applicant: ApplicantDTO | null = null;
  loading = true;
  notFound = false;

  /** The positions this person applied for, then the other open ones. */
  applications: JobApplicationDTO[] = [];
  otherOpenJobs: JobPostingDTO[] = [];
  selectedJobId: number | null = null;

  history: StatusHistoryDTO[] = [];
  actioning = false;
  actionError: string | null = null;

  tab: 'chat' | 'questions' = 'chat';

  // chat
  chatMessages: ChatMessage[] = [];
  chatInput = '';
  chatSending = false;
  replyStarted = false;
  chatError: string | null = null;
  private chatSub: Subscription | null = null;

  // interview questions
  questions: InterviewQuestions | null = null;
  questionsLoading = false;
  questionsError: string | null = null;

  readonly suggestions = [
    'Does this candidate have the experience required for this position?',
    'What are the main strengths and gaps of this profile?',
    'Summarise the career path in three lines.',
  ];

  ngOnInit(): void {
    this.applicantId = Number(this.route.snapshot.paramMap.get('id'));
    const jobIdParam = this.route.snapshot.queryParamMap.get('jobId');

    this.hr.getApplicantById(this.applicantId).subscribe({
      next: a => { this.applicant = a; this.loading = false; },
      error: () => { this.notFound = true; this.loading = false; }
    });

    this.hr.getApplicationsForApplicant(this.applicantId).subscribe(apps => {
      this.applications = apps;
      this.hr.getAllJobPostings().subscribe(jobs => {
        const applied = new Set(apps.map(a => a.jobId));
        this.otherOpenJobs = jobs.filter(j => j.status === 'OPEN' && !applied.has(j.jobId));
      });
      const initial = jobIdParam ? Number(jobIdParam) : apps[0]?.jobId ?? null;
      if (initial !== null) this.selectJob(initial);
    });
  }

  ngOnDestroy(): void {
    this.chatSub?.unsubscribe();
  }

  // ------------------------------------------------------------------ position

  get application(): JobApplicationDTO | null {
    return this.applications.find(a => a.jobId === this.selectedJobId) ?? null;
  }

  get selectedJobTitle(): string {
    return this.application?.jobTitle
      ?? this.otherOpenJobs.find(j => j.jobId === this.selectedJobId)?.title ?? '';
  }

  selectJob(jobId: number | null): void {
    this.selectedJobId = jobId;
    this.chatSub?.unsubscribe();
    this.chatSending = false;
    this.chatMessages = [];
    this.chatError = null;
    this.actionError = null;
    this.history = [];
    this.questions = null;
    this.questionsError = null;
    if (jobId === null) return;

    const app = this.application;
    if (app) this.hr.getApplicationHistory(app.applicationId).subscribe(h => this.history = h);

    this.ai.getApplicantChatHistory(this.applicantId, jobId).subscribe({
      next: res => { this.chatMessages = res.messages; this.scrollToBottom(); },
      error: () => { /* new conversation */ }
    });
  }

  private get status(): string {
    return (this.application?.status ?? '').toUpperCase();
  }

  get canInterview(): boolean { return CAN_INTERVIEW.includes(this.status); }
  get canOffer(): boolean { return CAN_OFFER.includes(this.status); }
  get canReject(): boolean { return CAN_REJECT.includes(this.status); }
  get canHire(): boolean { return this.status === 'OFFERED'; }

  act(action: 'interview' | 'offer' | 'reject'): void {
    const app = this.application;
    if (!app) return;
    if (action === 'reject' && !confirm('Reject this candidate for this position? An e-mail is sent to them.')) return;
    if (action === 'offer' && !confirm('Send an offer to this candidate? An e-mail is sent to them.')) return;

    this.actioning = true;
    this.actionError = null;
    const call = action === 'interview' ? this.hr.moveToInterview(app.applicationId)
      : action === 'offer' ? this.hr.moveToOffered(app.applicationId)
      : this.hr.rejectApplication(app.applicationId);
    call.subscribe({
      next: updated => {
        this.applications = this.applications.map(a => a.applicationId === updated.applicationId ? updated : a);
        this.hr.getApplicationHistory(updated.applicationId).subscribe(h => this.history = h);
        this.actioning = false;
        this.analytics.invalidate();
      },
      error: err => {
        this.actionError = errorMessage(err, 'The application could not be updated.');
        this.actioning = false;
      }
    });
  }

  hire(): void {
    this.router.navigate(['/dashboard/applicant', this.applicantId, 'hire'], {
      queryParams: { jobApplicationId: this.application?.applicationId ?? null, jobId: this.selectedJobId }
    });
  }

  // ------------------------------------------------------------------ chat (streamed)

  ask(text?: string): void {
    const message = (text ?? this.chatInput).trim();
    if (this.selectedJobId === null || this.chatSending || !message) return;

    this.chatMessages.push({ role: 'user', content: message });
    this.chatInput = '';
    this.chatSending = true;
    this.replyStarted = false;
    this.chatError = null;
    this.scrollToBottom();

    let reply: ChatMessage | null = null;
    this.chatSub = this.ai.streamApplicantChat(this.applicantId, this.selectedJobId, message).subscribe({
      next: chunk => {
        if (!reply) {
          reply = { role: 'assistant', content: '' };
          this.chatMessages.push(reply);
          this.replyStarted = true;
        }
        reply.content += chunk;
        this.scrollToBottom();
      },
      complete: () => this.chatSending = false,
      error: err => {
        if (!reply) this.chatMessages.pop(); // the question got no answer
        this.chatError = err?.message || 'The AI did not answer.';
        this.chatSending = false;
      }
    });
  }

  resetChat(): void {
    if (this.selectedJobId === null) return;
    this.chatSub?.unsubscribe();
    this.chatSending = false;
    this.ai.resetApplicantChat(this.applicantId, this.selectedJobId).subscribe(() => {
      this.chatMessages = [];
      this.chatError = null;
    });
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const el = this.chatScroll?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }

  // ------------------------------------------------------------------ interview questions

  generateQuestions(): void {
    if (this.selectedJobId === null) return;
    this.questionsLoading = true;
    this.questionsError = null;
    this.ai.interviewQuestions(this.applicantId, this.selectedJobId).subscribe({
      next: q => { this.questions = q; this.questionsLoading = false; },
      error: err => {
        this.questionsError = errorMessage(err, 'The questions could not be generated.');
        this.questionsLoading = false;
      }
    });
  }

  questionTone(type: string): string {
    switch (type) {
      case 'gap': return 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      case 'strength': return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
      default: return 'bg-sky-500/10 text-sky-300 border-sky-500/20';
    }
  }

  get backLink(): any[] {
    const fromJob = this.route.snapshot.queryParamMap.get('jobId');
    return fromJob ? ['/dashboard/jobs', Number(fromJob)] : ['/dashboard/applicants'];
  }
}

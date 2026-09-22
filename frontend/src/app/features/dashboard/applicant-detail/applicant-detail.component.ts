import { Component, ElementRef, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { HrService } from '../../../core/services/hr.service';
import { AiService } from '../../../core/services/ai.service';
import { ApplicantDTO, JobApplicationDTO, JobPostingDTO } from '../../../core/models/hr.model';
import { ChatMessage } from '../../../core/models/ai.model';

@Component({
  selector: 'app-applicant-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './applicant-detail.component.html'
})
export class ApplicantDetailComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private hrService = inject(HrService);
  private aiService = inject(AiService);

  @ViewChild('chatScroll') chatScroll?: ElementRef<HTMLElement>;

  applicantId!: number;
  applicant: ApplicantDTO | null = null;
  jobPostings: JobPostingDTO[] = [];
  selectedJobId: number | null = null;
  selectedJob: JobPostingDTO | null = null;
  jobFixed = false;

  application: JobApplicationDTO | null = null;
  actioning = false;
  actionError: string | null = null;

  loading = true;
  error = false;

  chatMessages: ChatMessage[] = [];
  chatInput = '';
  chatSending = false;
  replyStarted = false;
  chatError: string | null = null;
  private chatSub: Subscription | null = null;

  ngOnInit(): void {
    this.applicantId = Number(this.route.snapshot.paramMap.get('id'));
    const jobIdParam = this.route.snapshot.queryParamMap.get('jobId');

    this.hrService.getApplicantById(this.applicantId).subscribe({
      next: (a) => { this.applicant = a; this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });

    this.hrService.getAllJobPostings().subscribe(jobs => {
      this.jobPostings = jobs.filter(j => !j.status || j.status.toUpperCase() === 'OPEN');

      if (jobIdParam) {
        this.selectedJobId = Number(jobIdParam);
        // look up in ALL jobs so the context still shows if the job is no longer open
        this.selectedJob = jobs.find(j => j.jobId === this.selectedJobId) ?? null;
        this.jobFixed = true;
        this.onJobSelected();
      }
    });
  }

  ngOnDestroy(): void {
    this.chatSub?.unsubscribe();
  }

  // ---------- job / application ----------

  onJobSelected(): void {
    if (!this.jobFixed) {
      this.selectedJob = this.jobPostings.find(j => j.jobId === this.selectedJobId) ?? null;
    }
    this.chatSub?.unsubscribe();
    this.chatSending = false;
    this.chatMessages = [];
    this.chatError = null;
    this.actionError = null;
    this.application = null;

    if (this.selectedJobId === null) return;
    const jobId = this.selectedJobId;

    this.hrService.getAllJobApplications().subscribe(apps => {
      if (this.selectedJobId !== jobId) return;   // job changed meanwhile
      this.application = apps.find(a => a.jobId === jobId && a.applicantId === this.applicantId) ?? null;
    });

    this.aiService.getApplicantChatHistory(this.applicantId, jobId).subscribe({
      next: (res) => { this.chatMessages = res.messages; this.scrollToBottom(); },
      error: () => { /* fresh session */ }
    });
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

  get status(): string {
    return (this.application?.status ?? '').toUpperCase();
  }

  /** Offered/rejected are final: no more actions. */
  get isFinal(): boolean {
    return this.status === 'OFFERED' || this.status === 'REJECTED';
  }

  get canInterview(): boolean {
    return !!this.application && !this.isFinal && this.status !== 'INTERVIEWING';
  }

  interview(): void {
    if (!this.application) return;
    this.actioning = true;
    this.actionError = null;
    this.hrService.moveToInterview(this.application.applicationId).subscribe({
      next: (updated) => { this.application = updated; this.actioning = false; },
      error: () => { this.actionError = 'Could not update the application.'; this.actioning = false; }
    });
  }

  goToHire(): void {
    this.router.navigate(['/dashboard/recruitment/hire', this.applicantId], {
      queryParams: {
        jobApplicationId: this.application?.applicationId ?? null,
        jobId: this.selectedJobId
      }
    });
  }

  reject(): void {
    if (!this.application) return;
    if (!confirm('Reject this candidate for this position?')) return;
    this.actioning = true;
    this.actionError = null;
    this.hrService.rejectApplication(this.application.applicationId).subscribe({
      next: (updated) => { this.application = updated; this.actioning = false; },
      error: () => { this.actionError = 'Could not update the application.'; this.actioning = false; }
    });
  }

  // ---------- chat (streamed) ----------

  sendChatMessage(): void {
    if (this.selectedJobId === null || this.chatSending || !this.chatInput.trim()) return;

    const userMessage = this.chatInput.trim();
    this.chatMessages.push({ role: 'user', content: userMessage });
    this.chatInput = '';
    this.chatSending = true;
    this.replyStarted = false;
    this.chatError = null;
    this.scrollToBottom();

    let reply: ChatMessage | null = null;

    this.chatSub = this.aiService
      .streamApplicantChat(this.applicantId, this.selectedJobId, userMessage)
      .subscribe({
        next: (chunk) => {
          if (!reply) {
            reply = { role: 'assistant', content: '' };
            this.chatMessages.push(reply);
            this.replyStarted = true;
          }
          reply.content += chunk;
          this.scrollToBottom();
        },
        complete: () => { this.chatSending = false; },
        error: (err) => {
          if (!reply) this.chatMessages.pop();   // question never got an answer
          this.chatError = err?.message || 'Unknown error';
          this.chatSending = false;
        }
      });
  }

  resetChat(): void {
    if (this.selectedJobId === null) return;
    this.chatSub?.unsubscribe();
    this.chatSending = false;
    this.aiService.resetApplicantChat(this.applicantId, this.selectedJobId).subscribe(() => {
      this.chatMessages = [];
      this.chatError = null;
    });
  }

  /** Converts the LLM's lightweight markdown (**bold**, *italic*, "- " bullets,
   *  blank-line paragraphs) into safe HTML for [innerHTML]. Angular's default
   *  sanitizer allows strong/em/ul/li/p, so no DomSanitizer bypass is needed.
   *  Kept in sync with the identical method in ai-assistant.component.ts. */
  formatMessage(text: string | undefined | null): string {
    if (!text) return '';

    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    html = html
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>');

    const lines = html.split('\n');
    const out: string[] = [];
    let inList = false;

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (line.startsWith('- ')) {
        if (!inList) { out.push('<ul class="list-disc pl-4 space-y-0.5 mt-1">'); inList = true; }
        out.push(`<li>${line.slice(2)}</li>`);
      } else {
        if (inList) { out.push('</ul>'); inList = false; }
        if (line) out.push(`<p class="mt-1 first:mt-0">${line}</p>`);
      }
    }
    if (inList) out.push('</ul>');

    return out.join('');
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const el = this.chatScroll?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }

  goBack(): void {
    if (this.jobFixed && this.selectedJobId !== null) {
      this.router.navigate(['/dashboard/recruitment/job', this.selectedJobId]);
    } else {
      this.router.navigate(['/dashboard']);
    }
  }
}
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { AiService } from '../../../core/services/ai.service';
import { ApplicantDTO, JobPostingDTO } from '../../../core/models/hr.model';
import { FormsModule } from '@angular/forms';
import { ChatMessage } from '../../../core/models/ai.model';

@Component({
  selector: 'app-applicant-detail',
  standalone: true,
  imports: [CommonModule,FormsModule],
  templateUrl: './applicant-detail.component.html'
})
export class ApplicantDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private hrService = inject(HrService);
  private aiService = inject(AiService);

  applicant: ApplicantDTO | null = null;
  jobPostings: JobPostingDTO[] = [];
  selectedJobId: number | null = null;

  loading = true;
  error = false;

  assessing = false;
  assessment: any = null;
  assessmentError: string | null = null;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    this.hrService.getApplicantById(id).subscribe({
      next: (a) => { this.applicant = a; this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });

    this.hrService.getAllJobPostings().subscribe(jobs => {
      this.jobPostings = jobs.filter(j => !j.status || j.status.toUpperCase() === 'OPEN');
    });
  }

  chatMessages: ChatMessage[] = [];
chatInput = '';
chatSending = false;
chatError: string | null = null;

onJobSelected(): void {
  this.chatMessages = [];
  this.chatError = null;
  if (this.selectedJobId !== null && this.applicant) {
    this.aiService.getApplicantChatHistory(this.applicant.applicantId, this.selectedJobId).subscribe({
      next: (res) => { this.chatMessages = res.messages; },
      error: () => { /* fresh session, nothing to load -- fine */ }
    });
  }
}

sendChatMessage(): void {
  if (!this.applicant || this.selectedJobId === null || !this.chatInput.trim()) return;

  const userMessage = this.chatInput.trim();
  this.chatMessages.push({ role: 'user', content: userMessage });
  this.chatInput = '';
  this.chatSending = true;
  this.chatError = null;

  this.aiService.sendApplicantChatMessage(this.applicant.applicantId, this.selectedJobId, userMessage).subscribe({
    next: (res) => {
      this.chatMessages.push({ role: 'assistant', content: res.reply });
      this.chatSending = false;
    },
    error: (err) => {
      this.chatError = err?.error?.detail || 'Erreur inconnue';
      this.chatSending = false;
    }
  });
}

resetChat(): void {
  if (!this.applicant || this.selectedJobId === null) return;
  this.aiService.resetApplicantChat(this.applicant.applicantId, this.selectedJobId).subscribe(() => {
    this.chatMessages = [];
  });
}
  verdictClass(verdict: string): string {
    if (verdict === 'Strong fit') return 'text-teal-400';
    if (verdict === 'Possible fit') return 'text-amber-400';
    return 'text-rose-400';
  }

  goBack(): void {
    this.router.navigate(['/dashboard/recruitment']);
  }
}
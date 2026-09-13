import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AiService } from '../../../core/services/ai.service';
import { HrService, ApplicantWithCvStatus } from '../../../core/services/hr.service';

@Component({
  selector: 'app-applicant-cv-manager',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './applicant-cv-manager.component.html'
})
export class ApplicantCvManagerComponent implements OnInit {
  private hrService = inject(HrService);
  private aiService = inject(AiService);

  applicants: ApplicantWithCvStatus[] = [];
  loading = true;
  error = false;
  processingId: number | null = null;
  processErrorId: number | null = null;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = false;
    this.hrService.getApplicantsWithCvStatus().subscribe({
      next: (data) => { this.applicants = data; this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  processCv(applicantId: number): void {
    this.processingId = applicantId;
    this.processErrorId = null;

    this.aiService.processCv(applicantId).subscribe({
      next: () => {
        this.processingId = null;
        const applicant = this.applicants.find(a => a.applicantId === applicantId);
        if (applicant) applicant.isProcessed = true; // update in place, no full reload needed
      },
      error: () => {
        this.processingId = null;
        this.processErrorId = applicantId;
      }
    });
  }
}
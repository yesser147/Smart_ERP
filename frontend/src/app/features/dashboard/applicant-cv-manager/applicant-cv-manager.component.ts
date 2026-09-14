import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiService } from '../../../core/services/ai.service';
import { HrService, ApplicantWithCvStatus } from '../../../core/services/hr.service';

@Component({
  selector: 'app-applicant-cv-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
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
  processErrorMessage: string | null = null;

  searchTerm = '';
  showLastTenOnly = false;

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

  get filteredApplicants(): ApplicantWithCvStatus[] {
    let result = [...this.applicants].sort((a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );

    if (this.showLastTenOnly) result = result.slice(0, 10);

    const term = this.searchTerm.trim().toLowerCase();
    if (term) {
      result = result.filter(a =>
        `${a.firstName} ${a.lastName}`.toLowerCase().includes(term) ||
        a.email.toLowerCase().includes(term)
      );
    }

    return result;
  }

  processCv(applicantId: number): void {
    this.processingId = applicantId;
    this.processErrorId = null;
    this.processErrorMessage = null; // NEW field

    this.aiService.processCv(applicantId).subscribe({
      next: () => {
        this.processingId = null;
        const applicant = this.applicants.find(a => a.applicantId === applicantId);
        if (applicant) applicant.isProcessed = true;
      },
      error: (err) => {
        this.processingId = null;
        this.processErrorId = applicantId;
        // FastAPI's HTTPException serializes as { "detail": "..." }
        this.processErrorMessage = err?.error?.detail || 'Erreur inconnue';
      }
    });
  }
}
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiService } from '../../../core/services/ai.service';
import { HrService, ApplicantWithCvStatus } from '../../../core/services/hr.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-applicant-cv-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './applicant-cv-manager.component.html'
})
export class ApplicantCvManagerComponent implements OnInit {
  private hrService = inject(HrService);
  private aiService = inject(AiService);
    private router = inject(Router);

  applicants: ApplicantWithCvStatus[] = [];
  loading = true;
  error = false;
  processingId: number | null = null;
  processErrorId: number | null = null;
  processErrorMessage: string | null = null;

  searchTerm = '';
  showLastTenOnly = false;

  sortColumn: 'name' | 'createdAt' = 'createdAt';
  sortDirection: 'asc' | 'desc' = 'desc';

  pageSize = 25;
  currentPage = 1;

  onSearchOrFilterChange(): void {
    this.currentPage = 1;
  }

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

  toggleSort(column: 'name' | 'createdAt'): void {
    if (this.sortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortDirection = column === 'createdAt' ? 'desc' : 'asc';
    }
    this.currentPage = 1;
  }

  get filteredApplicants(): ApplicantWithCvStatus[] {
    let result = [...this.applicants];

    const term = this.searchTerm.trim().toLowerCase();
    if (term) {
      result = result.filter(a =>
        `${a.firstName} ${a.lastName}`.toLowerCase().includes(term) ||
        a.email.toLowerCase().includes(term)
      );
    }

    if (this.sortColumn === 'name') {
      result.sort((a, b) => {
        const cmp = `${a.firstName} ${a.lastName}`.localeCompare(`${b.firstName} ${b.lastName}`);
        return this.sortDirection === 'asc' ? cmp : -cmp;
      });
    } else {
      result.sort((a, b) => {
        const da = new Date(a.createdAt).getTime();
        const db = new Date(b.createdAt).getTime();
        return this.sortDirection === 'asc' ? da - db : db - da;
      });
    }

    if (this.showLastTenOnly) result = result.slice(0, 10);

    return result;
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filteredApplicants.length / this.pageSize));
  }

  get paginatedApplicants(): ApplicantWithCvStatus[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filteredApplicants.slice(start, start + this.pageSize);
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) this.currentPage++;
  }

  prevPage(): void {
    if (this.currentPage > 1) this.currentPage--;
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
goToDetail(applicantId: number): void {
  console.log('Navigating to applicant:', applicantId);
  this.router.navigate(['/dashboard/applicant', applicantId]);
}
}
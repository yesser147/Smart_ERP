import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { AiService } from '../../../core/services/ai.service';
import { ApplicantDTO, JobPostingDTO } from '../../../core/models/hr.model';
import { FormsModule } from '@angular/forms';

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

  assessFit(): void {
    if (!this.applicant || this.selectedJobId === null) return;
    this.assessing = true;
    this.assessment = null;
    this.assessmentError = null;

    this.aiService.assessApplicantFit(this.applicant.applicantId, this.selectedJobId).subscribe({
      next: (res) => { this.assessment = res; this.assessing = false; },
      error: (err) => {
        this.assessmentError = err?.error?.detail || 'Erreur inconnue';
        this.assessing = false;
      }
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
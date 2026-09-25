import { Component, OnInit, ViewChild, inject } from '@angular/core';
import { DecimalPipe, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { forkJoin } from 'rxjs';

import { HrService } from '../../../core/services/hr.service';
import { AiService } from '../../../core/services/ai.service';
import {
  EmployeeDTO, EmployeeTrainingDTO, EngagementSurveyDTO, PerformanceReviewDTO, SalaryHistoryDTO
} from '../../../core/models/hr.model';
import { EmployeeRisk } from '../../../core/models/ai.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';
import { featureLabel } from '../../../shared/utils/labels';
import { EmployeeFileComponent } from '../employee-file/employee-file.component';

@Component({
  selector: 'app-employee-detail',
  standalone: true,
  imports: [DecimalPipe, NgClass, FormsModule, PageHeaderComponent, IconComponent, EmployeeFileComponent],
  templateUrl: './employee-detail.component.html'
})
export class EmployeeDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private hr = inject(HrService);
  private ai = inject(AiService);

  id!: number;
  employee: EmployeeDTO | null = null;
  salaryHistory: SalaryHistoryDTO[] = [];
  trainings: EmployeeTrainingDTO[] = [];
  surveys: EngagementSurveyDTO[] = [];
  reviews: PerformanceReviewDTO[] = [];
  loading = true;
  notFound = false;

  // AI risk (active employees only)
  risk: EmployeeRisk | null = null;
  riskState: 'loading' | 'ready' | 'none' | 'error' = 'loading';
  riskMessage = '';

  // new review
  showReviewForm = false;
  reviewRating = 3;
  reviewComments = '';
  savingReview = false;
  reviewError: string | null = null;

  readonly featureLabel = featureLabel;

  @ViewChild(EmployeeFileComponent) file?: EmployeeFileComponent;

  openReviewForm(): void {
    this.showReviewForm = true;
    if (this.file) this.file.tab = 'performance';
  }

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    forkJoin({
      employee: this.hr.getEmployeeById(this.id),
      salary: this.hr.getEmployeeSalaryHistory(this.id),
      trainings: this.hr.getEmployeeTrainings(this.id),
      surveys: this.hr.getEmployeeSurveys(this.id),
      reviews: this.hr.getEmployeeReviews(this.id),
    }).subscribe({
      next: d => {
        this.employee = d.employee;
        this.salaryHistory = d.salary;
        this.trainings = d.trainings;
        this.surveys = d.surveys;
        this.reviews = d.reviews;
        this.loading = false;
        this.loadRisk();
      },
      error: () => { this.notFound = true; this.loading = false; }
    });
  }

  private loadRisk(): void {
    if ((this.employee?.employeeStatus ?? '').toLowerCase().includes('terminat')) {
      this.riskState = 'none';
      this.riskMessage = 'No risk score: this person has left the company.';
      return;
    }
    this.ai.getEmployeeRisk(this.id).subscribe({
      next: r => { this.risk = r; this.riskState = 'ready'; },
      error: err => {
        this.riskState = err?.status === 404 ? 'none' : 'error';
        this.riskMessage = errorMessage(err, 'The AI engine is not reachable.');
      }
    });
  }

  get riskPct(): number {
    return Math.round((this.risk?.risk_score ?? 0) * 100);
  }

  get riskTone(): string {
    if (!this.risk) return '';
    if (this.risk.high_risk) return 'text-rose-300';
    return this.risk.risk_score >= this.risk.threshold * 0.6 ? 'text-amber-300' : 'text-emerald-300';
  }

  get riskBar(): string {
    if (!this.risk) return '';
    if (this.risk.high_risk) return 'bg-rose-400';
    return this.risk.risk_score >= this.risk.threshold * 0.6 ? 'bg-amber-400' : 'bg-emerald-400';
  }

  saveReview(): void {
    this.savingReview = true;
    this.reviewError = null;
    this.hr.addEmployeeReview(this.id, this.reviewRating, this.reviewComments.trim()).subscribe({
      next: r => {
        this.reviews = [r, ...this.reviews];
        this.savingReview = false;
        this.showReviewForm = false;
        this.reviewComments = '';
        this.reviewRating = 3;
      },
      error: err => {
        this.reviewError = errorMessage(err, 'The review could not be saved.');
        this.savingReview = false;
      }
    });
  }
}

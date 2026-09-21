// employee-detail.component.ts
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { HrService } from '../../../core/services/hr.service';
import { EmployeeDTO, SalaryHistoryDTO, EmployeeTrainingDTO, EngagementSurveyDTO } from '../../../core/models/hr.model';

@Component({
  selector: 'app-employee-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './employee-detail.component.html'
})
export class EmployeeDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private hrService = inject(HrService);

  employee: EmployeeDTO | null = null;
  salaryHistory: SalaryHistoryDTO[] = [];
  trainings: EmployeeTrainingDTO[] = [];
  surveys: EngagementSurveyDTO[] = [];

  loading = true;
  error = false;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    forkJoin({
      employee: this.hrService.getEmployeeById(id),
      salary: this.hrService.getAllSalaryHistory(),
      trainings: this.hrService.getAllEmployeeTrainings(),
      surveys: this.hrService.getAllEngagementSurveys()
    }).subscribe({
      next: ({ employee, salary, trainings, surveys }) => {
        this.employee = employee;
        this.salaryHistory = salary
          .filter(s => s.employeeId === id)
          .sort((a, b) => new Date(b.effectiveDate).getTime() - new Date(a.effectiveDate).getTime());
        this.trainings = trainings.filter(t => t.employeeId === id);
        this.surveys = surveys
          .filter(s => s.employeeId === id)
          .sort((a, b) => new Date(b.surveyDate).getTime() - new Date(a.surveyDate).getTime());
        this.loading = false;
      },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }

  statusClass(status: string | undefined): string {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
      case 'ON LEAVE':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'TERMINATED':
      case 'TERMINATED FOR CAUSE':
      case 'VOLUNTARILY TERMINATED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'FUTURE START':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  }

  performanceClass(score: string | undefined): string {
    const s = score?.toUpperCase() ?? '';
    if (s.includes('EXCEED')) return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
    if (s.includes('MEET')) return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
    if (s.includes('BELOW') || s.includes('NEEDS')) return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  }

  get tenureYears(): number | null {
    if (!this.employee?.startDate) return null;
    const start = new Date(this.employee.startDate).getTime();
    const end = this.employee.exitDate ? new Date(this.employee.exitDate).getTime() : Date.now();
    return Math.round(((end - start) / (365.25 * 24 * 3600 * 1000)) * 10) / 10;
  }

  get avgEngagement(): number | null {
    if (this.surveys.length === 0) return null;
    return Math.round((this.surveys.reduce((s, x) => s + (x.engagementScore ?? 0), 0) / this.surveys.length) * 10) / 10;
  }

  get avgSatisfaction(): number | null {
    if (this.surveys.length === 0) return null;
    return Math.round((this.surveys.reduce((s, x) => s + (x.satisfactionScore ?? 0), 0) / this.surveys.length) * 10) / 10;
  }

  get avgWlb(): number | null {
    if (this.surveys.length === 0) return null;
    return Math.round((this.surveys.reduce((s, x) => s + (x.workLifeBalanceScore ?? 0), 0) / this.surveys.length) * 10) / 10;
  }
  isTerminated(e: { employeeStatus?: string | null }): boolean {
    return (e.employeeStatus ?? '').toLowerCase().includes('terminat');
  }
}

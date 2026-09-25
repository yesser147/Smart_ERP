import { Component, OnInit, inject } from '@angular/core';
import { DecimalPipe, NgClass } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { DepartmentSummaryDTO } from '../../../core/models/analytics.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { turnoverTone } from '../department-list/department-list.component';

/** The teams of one department. */
@Component({
  selector: 'app-department-type-detail',
  standalone: true,
  imports: [DecimalPipe, NgClass, RouterLink, PageHeaderComponent],
  templateUrl: './department-type-detail.component.html'
})
export class DepartmentTypeDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private analytics = inject(AnalyticsService);

  departmentType = '';
  teams: DepartmentSummaryDTO[] = [];
  loading = true;
  error = false;
  readonly turnoverTone = turnoverTone;

  ngOnInit(): void {
    this.departmentType = this.route.snapshot.paramMap.get('type') ?? '';
    this.analytics.dashboard().subscribe({
      next: d => {
        this.teams = d.departmentSummary
          .filter(t => (t.departmentType || 'Unclassified') === this.departmentType)
          .sort((a, b) => (b.headcount ?? 0) - (a.headcount ?? 0));
        this.loading = false;
      },
      error: () => { this.error = true; this.loading = false; }
    });
  }

  get headcount(): number {
    return this.teams.reduce((s, t) => s + (t.headcount ?? 0), 0);
  }
}

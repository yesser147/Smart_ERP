import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AiService } from '../../../core/services/ai.service';
import { CvSearchResult } from '../../../core/models/ai.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

/** Semantic search in every analysed CV (pgvector), whatever the job applied for. */
@Component({
  selector: 'app-cv-search',
  standalone: true,
  imports: [FormsModule, RouterLink, PageHeaderComponent, IconComponent],
  templateUrl: './cv-search.component.html'
})
export class CvSearchComponent {
  private ai = inject(AiService);

  query = '';
  results: CvSearchResult[] | null = null;
  loading = false;
  error: string | null = null;

  readonly examples = [
    'Python developer with machine learning experience',
    'Accountant who knows SAP and financial reporting',
    'Sales manager in pharmaceuticals',
    'HR generalist, recruitment and payroll',
  ];

  search(q?: string): void {
    if (q !== undefined) this.query = q;
    const text = this.query.trim();
    if (text.length < 3) return;
    this.loading = true;
    this.error = null;
    this.ai.searchCvs(text, 25).subscribe({
      next: r => { this.results = r; this.loading = false; },
      error: err => {
        this.error = errorMessage(err, 'The search failed.');
        this.loading = false;
      }
    });
  }

  relevanceClass(r: number): string {
    if (r >= 70) return 'bg-emerald-400';
    if (r >= 45) return 'bg-amber-400';
    return 'bg-slate-500';
  }
}

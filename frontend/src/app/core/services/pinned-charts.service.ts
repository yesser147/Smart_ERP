import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { AiService } from './ai.service';
import { ChartSpec, SavedChart } from '../models/ai.model';

/** The charts pinned from the HR assistant ("My charts" on the Overview).
 *  Shared state, so pinning from the chat updates the dashboard at once. */
@Injectable({ providedIn: 'root' })
export class PinnedChartsService {
  private ai = inject(AiService);

  readonly charts = signal<SavedChart[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    this.ai.savedCharts().subscribe({
      next: list => { this.charts.set(list); this.loading.set(false); },
      error: () => { this.error.set(true); this.loading.set(false); }
    });
  }

  pin(body: { title: string; question: string; sql_query: string; chart: ChartSpec }): Observable<{ id: number }> {
    return this.ai.saveChart(body).pipe(tap(() => this.load()));
  }

  remove(id: number): void {
    this.ai.deleteChart(id).subscribe(() => this.charts.update(list => list.filter(c => c.id !== id)));
  }
}

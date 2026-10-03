import { Component, HostListener, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { PinnedChartsService } from '../../../core/services/pinned-charts.service';
import { SavedChart } from '../../../core/models/ai.model';
import { AiChartComponent } from '../../../shared/components/ai-chart/ai-chart.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

/** "My charts" on the Overview: charts pinned from the HR assistant.
 *  The saved SQL is re-run on every load, so the numbers are always current. */
@Component({
  selector: 'app-my-charts',
  standalone: true,
  imports: [DatePipe, AiChartComponent, IconComponent],
  template: `
    <section class="space-y-4">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h2 class="erp-section-title flex items-center gap-2"><app-icon name="sparkles" class="h-4 w-4 text-accent" /> My charts</h2>
          <p class="text-xs text-slate-500">Charts you pinned from the AI assistant, refreshed with live data.</p>
        </div>
        @if (pinned.charts().length) {
          <button type="button" class="erp-btn-secondary erp-btn-sm" (click)="pinned.load()" [disabled]="pinned.loading()">
            <app-icon name="arrow-path" class="h-4 w-4" [class.animate-spin]="pinned.loading()" /> Refresh
          </button>
        }
      </div>

      @if (pinned.error()) {
        <div class="erp-card p-5 text-sm text-rose-300">Your charts could not be loaded (is the AI engine running?).</div>
      } @else if (!pinned.charts().length) {
        @if (!pinned.loading()) {
          <div class="erp-card flex items-center gap-4 p-5">
            <div class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-accent/10 text-accent"><app-icon name="chart-bar" class="h-5 w-5" /></div>
            <p class="text-sm text-slate-400">
              Ask the assistant (bottom right) for any chart, e.g. <span class="text-slate-200">"average salary by department and gender"</span>,
              then click <span class="text-slate-200">Pin to dashboard</span> to keep it here.
            </p>
          </div>
        }
      } @else {
        <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
          @for (c of pinned.charts(); track c.id) {
            <div class="erp-card overflow-hidden">
              <div class="flex items-start justify-between gap-3 px-4 pt-4">
                <div class="min-w-0">
                  <p class="truncate font-medium text-white">{{ c.title }}</p>
                  <p class="truncate text-xs text-slate-500" [title]="c.question">{{ c.question }}</p>
                </div>
                <div class="flex shrink-0 items-center gap-1">
                  @if (!c.error && c.rows.length) {
                    <button type="button" class="erp-icon-btn h-8 w-8" title="Enlarge" (click)="expanded = c"><app-icon name="external" class="h-4 w-4" /></button>
                  }
                  <button type="button" class="erp-icon-btn h-8 w-8 hover:text-rose-300" title="Remove from dashboard" (click)="remove(c)">
                    <app-icon name="x" class="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div class="px-2 pb-2">
                @if (c.error) {
                  <p class="px-2 py-8 text-center text-sm text-rose-300">{{ c.error }}</p>
                } @else if (!c.rows.length) {
                  <p class="px-2 py-8 text-center text-sm text-slate-500">The query returns no data right now.</p>
                } @else {
                  <app-ai-chart [spec]="c.chart" [rows]="c.rows" [height]="270" />
                }
              </div>
              @if (c.created_at) {
                <p class="border-t border-line px-4 py-2 text-[11px] text-slate-600">Pinned {{ c.created_at | date:'mediumDate' }}</p>
              }
            </div>
          }
        </div>
      }
    </section>

    @if (expanded; as c) {
      <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" (click)="expanded = null">
        <div class="w-full max-w-5xl rounded-card border border-line bg-surface shadow-pop animate-fade-in" (click)="$event.stopPropagation()">
          <div class="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
            <div class="min-w-0">
              <p class="truncate font-semibold text-white">{{ c.title }}</p>
              <p class="truncate text-xs text-slate-500">{{ c.question }}</p>
            </div>
            <button type="button" class="erp-icon-btn" (click)="expanded = null" aria-label="Close"><app-icon name="x" class="h-5 w-5" /></button>
          </div>
          <div class="p-4"><app-ai-chart [spec]="c.chart" [rows]="c.rows" [height]="460" /></div>
        </div>
      </div>
    }
  `
})
export class MyChartsComponent implements OnInit {
  readonly pinned = inject(PinnedChartsService);
  expanded: SavedChart | null = null;

  ngOnInit(): void {
    this.pinned.load();
  }

  @HostListener('document:keydown.escape')
  close(): void {
    this.expanded = null;
  }

  remove(c: SavedChart): void {
    if (confirm(`Remove "${c.title}" from your dashboard?`)) this.pinned.remove(c.id);
  }
}

import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from '../icon/icon.component';

/** Title block at the top of every page; buttons go in as content. */
@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [IconComponent, RouterLink],
  template: `
    @if (backLink) {
      <a [routerLink]="backLink" class="erp-btn-ghost mb-3 no-print">
        <app-icon name="arrow-left" class="h-4 w-4" /> {{ backLabel }}
      </a>
    }
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div class="flex items-start gap-3 min-w-0">
        @if (icon) {
          <div class="hidden sm:flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent-muted text-accent ring-1 ring-accent/20">
            <app-icon [name]="icon" class="h-5 w-5" />
          </div>
        }
        <div class="min-w-0">
          <h1 class="erp-page-title truncate">{{ title }}</h1>
          @if (subtitle) {
            <p class="text-sm text-slate-400 mt-1">{{ subtitle }}</p>
          }
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2 no-print">
        <ng-content />
      </div>
    </div>
  `
})
export class PageHeaderComponent {
  @Input({ required: true }) title = '';
  @Input() subtitle = '';
  @Input() icon = '';
  @Input() backLink: string | any[] | null = null;
  @Input() backLabel = 'Back';
}

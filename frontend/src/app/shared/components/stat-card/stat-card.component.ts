import { Component, Input } from '@angular/core';
import { NgClass } from '@angular/common';
import { IconComponent } from '../icon/icon.component';

export type StatTone = 'sky' | 'emerald' | 'amber' | 'rose' | 'violet' | 'slate';

const TONES: Record<StatTone, { icon: string; value: string }> = {
  sky:     { icon: 'bg-sky-500/10 text-sky-400 ring-sky-500/20',             value: 'text-white' },
  emerald: { icon: 'bg-emerald-500/10 text-emerald-400 ring-emerald-500/20', value: 'text-white' },
  amber:   { icon: 'bg-amber-500/10 text-amber-400 ring-amber-500/20',       value: 'text-white' },
  rose:    { icon: 'bg-rose-500/10 text-rose-400 ring-rose-500/20',          value: 'text-white' },
  violet:  { icon: 'bg-violet-500/10 text-violet-400 ring-violet-500/20',    value: 'text-white' },
  slate:   { icon: 'bg-slate-500/10 text-slate-300 ring-slate-500/20',       value: 'text-white' },
};

@Component({
  selector: 'app-stat-card',
  standalone: true,
  imports: [NgClass, IconComponent],
  template: `
    <div class="erp-card p-5 h-full">
      <div class="flex items-start justify-between gap-3">
        <p class="erp-kpi-label">{{ label }}</p>
        @if (icon) {
          <span class="flex h-9 w-9 items-center justify-center rounded-lg ring-1" [ngClass]="tone.icon">
            <app-icon [name]="icon" class="h-[18px] w-[18px]" />
          </span>
        }
      </div>
      <p class="erp-kpi" [ngClass]="tone.value">{{ value }}</p>
      @if (meta) {
        <p class="erp-kpi-meta">{{ meta }}</p>
      }
    </div>
  `
})
export class StatCardComponent {
  @Input({ required: true }) label = '';
  @Input() value: string | number | null = '—';
  @Input() meta = '';
  @Input() icon = '';
  @Input() set color(c: StatTone) { this.tone = TONES[c] ?? TONES.sky; }
  tone = TONES.sky;
}

import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from '../../shared/components/icon/icon.component';

/** Split screen used by the sign-in pages: product panel + form card. */
@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <div class="min-h-screen grid lg:grid-cols-2 bg-canvas">
      <!-- product panel -->
      <aside class="relative hidden lg:flex flex-col justify-between overflow-hidden border-r border-line bg-sidebar p-12">
        <div aria-hidden="true" class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(56,189,248,0.18),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(129,140,248,0.16),transparent_55%)]"></div>
        <div aria-hidden="true" class="absolute inset-0 opacity-[0.07] [background-image:linear-gradient(#94a3b8_1px,transparent_1px),linear-gradient(90deg,#94a3b8_1px,transparent_1px)] [background-size:36px_36px]"></div>

        <a routerLink="/careers" class="relative flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-from to-brand-to shadow-glow">
            <img src="assets/images/nexus.svg" alt="" class="h-7 w-7" />
          </span>
          <span class="text-lg font-semibold text-white">Nexus ERP</span>
        </a>

        <div class="relative max-w-md">
          <h2 class="text-3xl font-semibold tracking-tight text-white leading-tight">The HR platform that tells you what the numbers mean.</h2>
          <ul class="mt-8 space-y-4">
            @for (f of features; track f.title) {
              <li class="flex gap-3">
                <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5 text-accent ring-1 ring-white/10">
                  <app-icon [name]="f.icon" class="h-[18px] w-[18px]" />
                </span>
                <span>
                  <span class="block text-sm font-medium text-white">{{ f.title }}</span>
                  <span class="block text-sm text-slate-400">{{ f.text }}</span>
                </span>
              </li>
            }
          </ul>
        </div>

        <p class="relative text-xs text-slate-500">© Nexus · Smart ERP</p>
      </aside>

      <!-- form -->
      <main class="flex items-center justify-center p-6 sm:p-10">
        <div class="w-full max-w-sm animate-fade-in">
          <div class="lg:hidden mb-8 flex items-center gap-3">
            <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-from to-brand-to">
              <img src="assets/images/nexus.svg" alt="" class="h-7 w-7" />
            </span>
            <span class="text-lg font-semibold text-white">Nexus ERP</span>
          </div>
          <h1 class="text-2xl font-semibold tracking-tight text-white">{{ title }}</h1>
          @if (subtitle) { <p class="mt-2 text-sm text-slate-400">{{ subtitle }}</p> }
          <div class="mt-8"><ng-content /></div>
        </div>
      </main>
    </div>
  `
})
export class AuthLayoutComponent {
  @Input({ required: true }) title = '';
  @Input() subtitle = '';

  readonly features = [
    { icon: 'chart-bar', title: 'Live workforce analytics', text: 'Headcount, turnover, pay equity and engagement in one place.' },
    { icon: 'shield-check', title: 'Attrition risk', text: 'A model that flags who may leave, and why.' },
    { icon: 'sparkles', title: 'AI recruiting', text: 'CVs read and ranked automatically, with interview questions ready.' },
  ];
}

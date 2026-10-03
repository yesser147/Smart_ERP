import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PublicService } from '../../core/services/public.service';
import { IconComponent } from '../../shared/components/icon/icon.component';

/** Public home page: candidates go to the careers site, employees to the sign-in page. */
@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <div class="relative min-h-screen overflow-hidden bg-canvas">
      <div aria-hidden="true" class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(56,189,248,0.16),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(129,140,248,0.14),transparent_55%)]"></div>
      <div aria-hidden="true" class="absolute inset-0 opacity-[0.06] [background-image:linear-gradient(#94a3b8_1px,transparent_1px),linear-gradient(90deg,#94a3b8_1px,transparent_1px)] [background-size:36px_36px]"></div>

      <header class="relative mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <span class="flex items-center gap-3">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-from to-brand-to shadow-glow">
            <img src="assets/images/nexus.svg" alt="" class="h-6 w-6" />
          </span>
          <span class="font-semibold text-white">Nexus</span>
        </span>
        <nav class="flex items-center gap-2">
          <a routerLink="/careers" class="erp-btn-ghost text-xs">Careers</a>
          <a routerLink="/auth/login" class="erp-btn-secondary erp-btn-sm">Sign in</a>
        </nav>
      </header>

      <main class="relative mx-auto max-w-5xl px-4 pb-16 pt-10 sm:px-6 sm:pt-20">
        <div class="text-center animate-fade-in">
          <p class="erp-kicker text-accent">Welcome to Nexus</p>
          <h1 class="mx-auto mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-5xl">How can we help you today?</h1>
          <p class="mx-auto mt-4 max-w-xl text-slate-400">Join our teams, or sign in to the HR platform.</p>
        </div>

        <div class="mt-12 grid gap-5 md:grid-cols-2">
          <a routerLink="/careers" class="group erp-card relative overflow-hidden p-7 transition-colors hover:border-accent/50">
            <span class="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent ring-1 ring-accent/20">
              <app-icon name="briefcase" class="h-6 w-6" />
            </span>
            <h2 class="mt-5 text-xl font-semibold text-white">I'm looking for a job</h2>
            <p class="mt-2 text-sm text-slate-400">
              Browse our open positions and apply in two minutes with your CV. No account needed.
            </p>
            <p class="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-accent">
              {{ openings === null ? 'See open positions' : openings + ' open position' + (openings === 1 ? '' : 's') }}
              <app-icon name="chevron-right" class="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </p>
          </a>

          <a routerLink="/auth/login" class="group erp-card relative overflow-hidden p-7 transition-colors hover:border-indigo-400/50">
            <span class="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-400/10 text-indigo-300 ring-1 ring-indigo-400/20">
              <app-icon name="user-circle" class="h-6 w-6" />
            </span>
            <h2 class="mt-5 text-xl font-semibold text-white">I work at Nexus</h2>
            <p class="mt-2 text-sm text-slate-400">
              Sign in to your space: leave requests and reviews, or the HR workspace with analytics and AI tools.
            </p>
            <p class="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-indigo-300">
              Employee sign-in
              <app-icon name="chevron-right" class="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </p>
          </a>
        </div>

        <p class="mt-14 text-center text-xs text-slate-600">© Nexus · Smart ERP</p>
      </main>
    </div>
  `
})
export class LandingComponent implements OnInit {
  private publicApi = inject(PublicService);
  openings: number | null = null;

  ngOnInit(): void {
    this.publicApi.openJobs().subscribe({ next: jobs => this.openings = jobs.length, error: () => { /* the link still works */ } });
  }
}

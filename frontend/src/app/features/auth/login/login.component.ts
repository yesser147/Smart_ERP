import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthLayoutComponent } from '../auth-layout.component';
import { errorMessage } from '../../../shared/utils/errors';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent],
  template: `
    <app-auth-layout title="Sign in" subtitle="Welcome back. Use your work e-mail.">
      <form [formGroup]="form" (ngSubmit)="submit()" class="space-y-5" novalidate>
        @if (error()) { <div class="erp-alert-error">{{ error() }}</div> }
        <div>
          <label class="erp-label" for="email">E-mail</label>
          <input id="email" type="email" formControlName="email" class="erp-input h-11" autocomplete="username" autofocus />
          @if (form.controls.email.touched && form.controls.email.invalid) {
            <p class="mt-1 text-xs text-rose-300">Enter a valid e-mail address.</p>
          }
        </div>
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="erp-label mb-0" for="password">Password</label>
            <a routerLink="/auth/forgot-password" class="text-xs text-accent hover:text-accent-hover">Forgot password?</a>
          </div>
          <input id="password" type="password" formControlName="password" class="erp-input h-11" autocomplete="current-password" />
          @if (form.controls.password.touched && form.controls.password.invalid) {
            <p class="mt-1 text-xs text-rose-300">Enter your password.</p>
          }
        </div>
        <button type="submit" class="erp-btn-primary w-full h-11" [disabled]="loading()">
          {{ loading() ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
      <p class="mt-8 text-center text-xs text-slate-500">
        Looking for a job? <a routerLink="/careers" class="text-accent hover:text-accent-hover">See our openings</a>
      </p>
    </app-auth-layout>
  `
})
export class LoginComponent {
  private fb = inject(NonNullableFormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  loading = signal(false);
  error = signal<string | null>(null);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => {
        const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
        // only in-app paths, never an absolute URL
        this.router.navigateByUrl(returnUrl?.startsWith('/dashboard') ? returnUrl : '/dashboard');
      },
      error: err => {
        this.loading.set(false);
        this.error.set(err?.status === 401 || err?.status === 403
          ? 'Wrong e-mail or password.'
          : errorMessage(err, 'Sign-in failed. Please try again.'));
      }
    });
  }
}

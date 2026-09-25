import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthLayoutComponent } from '../auth-layout.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, AuthLayoutComponent, IconComponent],
  template: `
    <app-auth-layout title="Reset your password" subtitle="We will e-mail you a link to choose a new one.">
      @if (sent()) {
        <div class="erp-alert-success">
          <app-icon name="mail" class="h-5 w-5 shrink-0" />
          <span>If an account exists for this address, a reset link is on its way. It is valid for 60 minutes.</span>
        </div>
      } @else {
        <form [formGroup]="form" (ngSubmit)="submit()" class="space-y-5" novalidate>
          @if (error()) { <div class="erp-alert-error">{{ error() }}</div> }
          <div>
            <label class="erp-label" for="email">E-mail</label>
            <input id="email" type="email" formControlName="email" class="erp-input h-11" autocomplete="username" autofocus />
            @if (form.controls.email.touched && form.controls.email.invalid) {
              <p class="mt-1 text-xs text-rose-300">Enter a valid e-mail address.</p>
            }
          </div>
          <button type="submit" class="erp-btn-primary w-full h-11" [disabled]="loading()">
            {{ loading() ? 'Sending...' : 'Send the link' }}
          </button>
        </form>
      }
      <a routerLink="/auth/login" class="erp-btn-ghost mt-8"><app-icon name="arrow-left" class="h-4 w-4" /> Back to sign in</a>
    </app-auth-layout>
  `
})
export class ForgotPasswordComponent {
  private fb = inject(NonNullableFormBuilder);
  private auth = inject(AuthService);

  loading = signal(false);
  sent = signal(false);
  error = signal<string | null>(null);

  form = this.fb.group({ email: ['', [Validators.required, Validators.email]] });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.auth.forgotPassword(this.form.getRawValue().email).subscribe({
      next: () => { this.loading.set(false); this.sent.set(true); },
      error: err => {
        this.loading.set(false);
        this.error.set(errorMessage(err, 'The request could not be sent. Please try again.'));
      }
    });
  }
}

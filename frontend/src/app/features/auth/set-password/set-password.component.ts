import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthLayoutComponent } from '../auth-layout.component';
import { errorMessage } from '../../../shared/utils/errors';

/** Opened from the activation / reset e-mail: /auth/set-password?token=... */
@Component({
  selector: 'app-set-password',
  standalone: true,
  imports: [FormsModule, RouterLink, AuthLayoutComponent],
  template: `
    <app-auth-layout title="Choose your password" subtitle="To activate your account or replace a forgotten password.">
      @if (!token) {
        <div class="erp-alert-error">This link is incomplete. Use the link from the e-mail, or ask for a new one.</div>
        <a routerLink="/auth/forgot-password" class="erp-btn-secondary w-full mt-4">Ask for a new link</a>
      } @else if (done()) {
        <div class="erp-alert-success">Your password is set. Redirecting to the sign-in page...</div>
      } @else {
        <form (ngSubmit)="submit()" class="space-y-5">
          @if (error()) { <div class="erp-alert-error">{{ error() }}</div> }
          <div>
            <label class="erp-label" for="pw">New password</label>
            <input id="pw" type="password" name="pw" [(ngModel)]="password" class="erp-input h-11" autocomplete="new-password" />
            <ul class="mt-2 space-y-1 text-xs">
              <li [class.text-emerald-300]="password.length >= 8" [class.text-slate-500]="password.length < 8">• At least 8 characters</li>
              <li [class.text-emerald-300]="hasLetter" [class.text-slate-500]="!hasLetter">• At least one letter</li>
              <li [class.text-emerald-300]="hasDigit" [class.text-slate-500]="!hasDigit">• At least one digit</li>
            </ul>
          </div>
          <div>
            <label class="erp-label" for="pw2">Confirm</label>
            <input id="pw2" type="password" name="pw2" [(ngModel)]="confirm" class="erp-input h-11" autocomplete="new-password" />
            @if (confirm && confirm !== password) { <p class="mt-1 text-xs text-rose-300">The passwords are different.</p> }
          </div>
          <button type="submit" class="erp-btn-primary w-full h-11" [disabled]="loading() || !valid">
            {{ loading() ? 'Saving...' : 'Save password' }}
          </button>
        </form>
      }
    </app-auth-layout>
  `
})
export class SetPasswordComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private auth = inject(AuthService);

  token = '';
  password = '';
  confirm = '';
  loading = signal(false);
  done = signal(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token') ?? '';
  }

  get hasLetter(): boolean { return /[A-Za-z]/.test(this.password); }
  get hasDigit(): boolean { return /[0-9]/.test(this.password); }

  /** Same rule as the backend (SetPasswordRequest). */
  get valid(): boolean {
    return this.password.length >= 8 && this.hasLetter && this.hasDigit && this.password === this.confirm;
  }

  submit(): void {
    if (!this.valid) return;
    this.loading.set(true);
    this.error.set(null);
    this.auth.setPassword({ token: this.token, newPassword: this.password }).subscribe({
      next: () => {
        this.done.set(true);
        setTimeout(() => this.router.navigate(['/auth/login']), 2000);
      },
      error: err => {
        this.loading.set(false);
        this.error.set(errorMessage(err, 'The password could not be saved. The link may have expired.'));
      }
    });
  }
}

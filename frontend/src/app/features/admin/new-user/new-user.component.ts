import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ROLE_LABELS, RoleName } from '../../../core/models/auth.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { errorMessage } from '../../../shared/utils/errors';

/** Admin: account without an employee file (e.g. an external HR consultant).
 *  Employees get their account automatically when they are hired. */
@Component({
  selector: 'app-new-user',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, PageHeaderComponent],
  template: `
    <div class="erp-page max-w-2xl">
      <app-page-header title="New account" icon="key" backLink="/dashboard/admin/users" backLabel="Users & roles"
                       subtitle="For people without an employee file. Hired employees get their account automatically." />

      <form [formGroup]="form" (ngSubmit)="submit()" class="erp-card">
        <div class="space-y-4 p-5">
          <div>
            <label class="erp-label" for="email">E-mail *</label>
            <input id="email" type="email" formControlName="email" class="erp-input" autocomplete="off" />
            @if (form.controls.email.invalid && form.controls.email.touched) { <p class="text-xs text-rose-300 mt-1">Enter a valid e-mail address.</p> }
          </div>
          <div>
            <label class="erp-label" for="password">Temporary password *</label>
            <input id="password" type="password" formControlName="password" class="erp-input" autocomplete="new-password" />
            <p class="text-xs mt-1" [class.text-rose-300]="form.controls.password.invalid && form.controls.password.touched"
               [class.text-slate-500]="!(form.controls.password.invalid && form.controls.password.touched)">
              At least 8 characters, with a letter and a digit. The person can change it with "Forgot password".
            </p>
          </div>
          <div>
            <label class="erp-label" for="role">Role *</label>
            <select id="role" formControlName="role" class="erp-input">
              @for (r of roles; track r) { <option [value]="r">{{ labels[r] }}</option> }
            </select>
          </div>
          @if (error()) { <div class="erp-alert-error">{{ error() }}</div> }
          @if (success()) { <div class="erp-alert-success">{{ success() }}</div> }
        </div>
        <div class="flex justify-end gap-2 border-t border-line px-5 py-4">
          <a routerLink="/dashboard/admin/users" class="erp-btn-secondary">Back</a>
          <button type="submit" class="erp-btn-primary" [disabled]="saving()">{{ saving() ? 'Creating...' : 'Create account' }}</button>
        </div>
      </form>
    </div>
  `
})
export class NewUserComponent {
  private fb = inject(NonNullableFormBuilder);
  private auth = inject(AuthService);

  readonly roles: RoleName[] = ['ROLE_HR_MANAGER', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_EMPLOYEE'];
  readonly labels = ROLE_LABELS;

  saving = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8), Validators.pattern(/^(?=.*[A-Za-z])(?=.*[0-9]).+$/)]],
    role: ['ROLE_HR_MANAGER' as RoleName, Validators.required]
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    this.success.set(null);
    this.auth.createUser(this.form.getRawValue()).subscribe({
      next: res => {
        this.saving.set(false);
        this.success.set(`Account ${res.email} created.`);
        this.form.reset({ email: '', password: '', role: 'ROLE_HR_MANAGER' });
      },
      error: err => {
        this.saving.set(false);
        this.error.set(errorMessage(err, 'The account could not be created.'));
      }
    });
  }
}

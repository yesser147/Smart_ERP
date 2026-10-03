import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged, switchMap, catchError, of } from 'rxjs';
import { AdminService, EmployeeOption } from '../../../core/services/admin.service';
import { ROLE_LABELS, RoleName } from '../../../core/models/auth.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

/** Admin: a login for an existing employee who has none yet. Every account belongs to an
 *  employee file; new hires get theirs automatically at the Hire step. */
@Component({
  selector: 'app-new-user',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, PageHeaderComponent, IconComponent],
  template: `
    <div class="erp-page max-w-2xl">
      <app-page-header title="New account" icon="key" backLink="/dashboard/admin/users" backLabel="Users & roles"
                       subtitle="Give an existing employee access to the platform. New hires get their account at the Hire step." />

      <form [formGroup]="form" (ngSubmit)="submit()" class="erp-card">
        <div class="space-y-4 p-5">
          <!-- 1. the employee -->
          <div>
            <label class="erp-label" for="employee">Employee *</label>
            @if (selected(); as e) {
              <div class="flex items-center justify-between gap-3 rounded-lg border border-accent/40 bg-accent/5 px-3 py-2.5">
                <div class="min-w-0">
                  <p class="truncate text-sm font-medium text-white">{{ e.name }}</p>
                  <p class="truncate text-xs text-slate-400">{{ e.title || '—' }}{{ e.team ? ' · ' + e.team : '' }}</p>
                </div>
                <button type="button" class="erp-btn-ghost text-xs" (click)="clearEmployee()">Change</button>
              </div>
            } @else {
              <div class="relative">
                <app-icon name="search" class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input id="employee" type="text" class="erp-input pl-9" placeholder="Search by name or job title..." autocomplete="off"
                       (input)="search$.next($any($event.target).value)" (focus)="search$.next(lastSearch)" />
              </div>
              <div class="mt-2 max-h-64 overflow-y-auto rounded-lg border border-line">
                @for (e of options(); track e.employeeId) {
                  <button type="button" class="flex w-full items-center justify-between gap-3 border-b border-line px-3 py-2 text-left last:border-0 hover:bg-white/5"
                          (click)="choose(e)">
                    <span class="min-w-0">
                      <span class="block truncate text-sm text-white">{{ e.name }}</span>
                      <span class="block truncate text-xs text-slate-500">{{ e.title || '—' }}{{ e.team ? ' · ' + e.team : '' }}</span>
                    </span>
                    <app-icon name="chevron-right" class="h-4 w-4 shrink-0 text-slate-500" />
                  </button>
                } @empty {
                  <p class="px-3 py-4 text-center text-xs text-slate-500">
                    @if (searching()) { Searching... }
                    @else if (lastSearch.trim()) { No current employee without an account matches "{{ lastSearch.trim() }}". }
                    @else { Every current employee already has an account. New hires get theirs at the Hire step. }
                  </p>
                }
              </div>
              <p class="mt-1 text-xs" [class.text-rose-300]="employeeMissing()" [class.text-slate-500]="!employeeMissing()">
                Only current employees who don't have an account yet are listed.
              </p>
            }
          </div>

          <!-- 2. the login -->
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
            <p class="text-xs text-slate-500 mt-1">{{ roleHelp[form.controls.role.value] }}</p>
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
export class NewUserComponent implements OnInit {
  private fb = inject(NonNullableFormBuilder);
  private admin = inject(AdminService);

  readonly roles: RoleName[] = ['ROLE_EMPLOYEE', 'ROLE_MANAGER', 'ROLE_HR_MANAGER', 'ROLE_ADMIN'];
  readonly labels = ROLE_LABELS;
  readonly roleHelp: Record<string, string> = {
    ROLE_EMPLOYEE: 'Sees only their own space: profile, leave requests, reviews.',
    ROLE_MANAGER: 'HR workspace: analytics, people, recruitment, AI tools.',
    ROLE_HR_MANAGER: 'HR workspace: analytics, people, recruitment, AI tools.',
    ROLE_ADMIN: 'Everything, plus users & roles, audit log and AI models.',
  };

  readonly search$ = new Subject<string>();
  lastSearch = '';
  options = signal<EmployeeOption[]>([]);
  searching = signal(false);
  selected = signal<EmployeeOption | null>(null);
  employeeMissing = signal(false);

  saving = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8), Validators.pattern(/^(?=.*[A-Za-z])(?=.*[0-9]).+$/)]],
    role: ['ROLE_EMPLOYEE' as RoleName, Validators.required]
  });

  ngOnInit(): void {
    this.search$.pipe(
      debounceTime(250),
      distinctUntilChanged(),
      switchMap(q => {
        this.lastSearch = q;
        this.searching.set(true);
        return this.admin.employeesWithoutAccount(q.trim()).pipe(catchError(() => of([])));
      })
    ).subscribe(list => {
      this.options.set(list);
      this.searching.set(false);
    });
    this.search$.next('');
  }

  choose(e: EmployeeOption): void {
    this.selected.set(e);
    this.employeeMissing.set(false);
  }

  clearEmployee(): void {
    this.selected.set(null);
  }

  submit(): void {
    const employee = this.selected();
    this.employeeMissing.set(!employee);
    if (this.form.invalid || !employee) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    this.success.set(null);
    this.admin.createAccount({ employeeId: employee.employeeId, ...this.form.getRawValue() }).subscribe({
      next: res => {
        this.saving.set(false);
        this.success.set(`Account ${res.email} created for ${employee.name}.`);
        this.form.reset({ email: '', password: '', role: 'ROLE_EMPLOYEE' });
        this.selected.set(null);
        this.options.update(list => list.filter(o => o.employeeId !== employee.employeeId));
      },
      error: err => {
        this.saving.set(false);
        this.error.set(errorMessage(err, 'The account could not be created.'));
      }
    });
  }
}

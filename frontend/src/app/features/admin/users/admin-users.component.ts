import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, debounceTime } from 'rxjs';

import { AdminService } from '../../../core/services/admin.service';
import { TokenService } from '../../../core/services/token.service';
import { AdminUserDTO } from '../../../core/models/hr.model';
import { ROLE_LABELS } from '../../../core/models/auth.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

const PAGE_SIZE = 25;

@Component({
  selector: 'app-admin-users',
  standalone: true,
  imports: [DatePipe, NgClass, FormsModule, RouterLink, PageHeaderComponent, IconComponent],
  templateUrl: './admin-users.component.html'
})
export class AdminUsersComponent implements OnInit {
  private admin = inject(AdminService);
  private destroyRef = inject(DestroyRef);
  readonly me = inject(TokenService).getUserInfo()?.userId;

  readonly roles = Object.keys(ROLE_LABELS);
  readonly labels = ROLE_LABELS;

  users: AdminUserDTO[] = [];
  total = 0;
  totalPages = 1;
  page = 0;
  search = '';
  role = '';
  loading = true;
  error: string | null = null;
  busy = new Set<string>();
  private search$ = new Subject<void>();

  ngOnInit(): void {
    this.search$.pipe(debounceTime(300), takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.page = 0;
      this.load();
    });
    this.load();
  }

  load(): void {
    this.loading = true;
    this.admin.users(this.page, PAGE_SIZE, this.search, this.role).subscribe({
      next: p => {
        this.users = p.content;
        this.total = p.totalElements;
        this.totalPages = Math.max(1, p.totalPages);
        this.loading = false;
      },
      error: err => { this.error = errorMessage(err, 'The accounts could not be loaded.'); this.loading = false; }
    });
  }

  onSearch(): void {
    this.search$.next();
  }

  onRoleFilter(): void {
    this.page = 0;
    this.load();
  }

  goTo(p: number): void {
    if (p < 0 || p >= this.totalPages) return;
    this.page = p;
    this.load();
  }

  roleTone(role: string): string {
    switch (role) {
      case 'ROLE_ADMIN': return 'bg-violet-500/10 text-violet-300 border-violet-500/20';
      case 'ROLE_HR_MANAGER': return 'bg-sky-500/10 text-sky-300 border-sky-500/20';
      case 'ROLE_MANAGER': return 'bg-teal-500/10 text-teal-300 border-teal-500/20';
      default: return 'bg-slate-500/10 text-slate-300 border-slate-500/20';
    }
  }

  private replace(updated: AdminUserDTO): void {
    this.users = this.users.map(u => (u.id === updated.id ? updated : u));
  }

  changeRole(u: AdminUserDTO, select: HTMLSelectElement): void {
    const role = select.value;
    if (role === u.role) return;
    if (!confirm(`Give ${u.email} the role "${ROLE_LABELS[role]}"?`)) {
      select.value = u.role;
      return;
    }
    this.busy.add(u.id);
    this.error = null;
    this.admin.changeRole(u.id, role).subscribe({
      next: updated => { this.replace(updated); this.busy.delete(u.id); },
      error: err => {
        this.error = errorMessage(err, 'The role could not be changed.');
        select.value = u.role;
        this.busy.delete(u.id);
      }
    });
  }

  toggleActive(u: AdminUserDTO): void {
    if (u.active && !confirm(`Deactivate ${u.email}? They will not be able to sign in.`)) return;
    this.busy.add(u.id);
    this.error = null;
    this.admin.setActive(u.id, !u.active).subscribe({
      next: updated => { this.replace(updated); this.busy.delete(u.id); },
      error: err => { this.error = errorMessage(err, 'The account could not be updated.'); this.busy.delete(u.id); }
    });
  }
}

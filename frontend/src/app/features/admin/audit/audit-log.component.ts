import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, debounceTime } from 'rxjs';

import { AdminService } from '../../../core/services/admin.service';
import { AuditLogDTO } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';

const PAGE_SIZE = 50;

/** Who did what: status changes, hires, role changes, approvals... */
@Component({
  selector: 'app-audit-log',
  standalone: true,
  imports: [DatePipe, FormsModule, PageHeaderComponent, IconComponent],
  template: `
    <div class="erp-page">
      <app-page-header title="Audit log" icon="clipboard" subtitle="Every sensitive action, with who did it and when" />

      <div class="erp-card overflow-hidden">
        <div class="p-4 border-b border-line">
          <div class="relative max-w-md">
            <app-icon name="search" class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input [(ngModel)]="search" (ngModelChange)="search$.next()" placeholder="Search user, action, details..." class="erp-input py-1.5 pl-8" />
          </div>
        </div>
        <div class="overflow-x-auto" [class.opacity-60]="loading">
          <table class="erp-table">
            <thead><tr><th>When</th><th>Who</th><th>Action</th><th>Object</th><th>Details</th></tr></thead>
            <tbody>
              @for (a of entries; track a.id) {
                <tr>
                  <td class="whitespace-nowrap text-slate-400">{{ a.createdAt | date:'d MMM y, HH:mm' }}</td>
                  <td class="text-slate-200">{{ a.actor }}</td>
                  <td><span class="erp-badge bg-slate-500/10 text-slate-200 border-slate-500/20 normal-case tracking-normal font-mono">{{ a.action }}</span></td>
                  <td class="text-slate-400 whitespace-nowrap">{{ a.entityType ? a.entityType + ' #' + a.entityId : '—' }}</td>
                  <td class="text-slate-400 max-w-md truncate" [title]="a.details || ''">{{ a.details || '—' }}</td>
                </tr>
              } @empty {
                <tr><td colspan="5" class="erp-empty">{{ loading ? 'Loading...' : 'Nothing recorded yet.' }}</td></tr>
              }
            </tbody>
          </table>
        </div>
        <div class="flex items-center justify-between px-4 py-3 border-t border-line text-xs text-slate-400">
          <span>{{ total }} entries · page {{ page + 1 }} of {{ totalPages }}</span>
          <div class="flex gap-2">
            <button type="button" class="erp-btn-secondary erp-btn-sm" (click)="goTo(page - 1)" [disabled]="page === 0">Previous</button>
            <button type="button" class="erp-btn-secondary erp-btn-sm" (click)="goTo(page + 1)" [disabled]="page >= totalPages - 1">Next</button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class AuditLogComponent implements OnInit {
  private admin = inject(AdminService);
  private destroyRef = inject(DestroyRef);

  entries: AuditLogDTO[] = [];
  total = 0;
  totalPages = 1;
  page = 0;
  search = '';
  loading = true;
  readonly search$ = new Subject<void>();

  ngOnInit(): void {
    this.search$.pipe(debounceTime(300), takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.page = 0;
      this.load();
    });
    this.load();
  }

  load(): void {
    this.loading = true;
    this.admin.audit(this.page, PAGE_SIZE, this.search).subscribe({
      next: p => {
        this.entries = p.content;
        this.total = p.totalElements;
        this.totalPages = Math.max(1, p.totalPages);
        this.loading = false;
      },
      error: () => this.loading = false
    });
  }

  goTo(p: number): void {
    if (p < 0 || p >= this.totalPages) return;
    this.page = p;
    this.load();
  }
}

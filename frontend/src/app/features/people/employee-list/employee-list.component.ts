import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, debounceTime, forkJoin, map, of, switchMap } from 'rxjs';

import { HrService } from '../../../core/services/hr.service';
import { EmployeeDTO, PageResponse } from '../../../core/models/hr.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { saveFile, toCsv } from '../../../shared/utils/download';

type SortColumn = 'name' | 'title' | 'department' | 'employeeStatus' | 'salary' | 'startDate';

const EXPORT_COLUMNS = [
  { key: 'employeeId', label: 'ID' }, { key: 'firstName', label: 'First name' }, { key: 'lastName', label: 'Last name' },
  { key: 'title', label: 'Title' }, { key: 'departmentName', label: 'Team' }, { key: 'managerName', label: 'Manager' },
  { key: 'employeeStatus', label: 'Status' }, { key: 'employeeType', label: 'Type' }, { key: 'location', label: 'Location' },
  { key: 'startDate', label: 'Start date' }, { key: 'exitDate', label: 'Exit date' }, { key: 'salary', label: 'Salary' },
  { key: 'performanceScore', label: 'Performance' },
];

@Component({
  selector: 'app-employee-list',
  standalone: true,
  imports: [DatePipe, DecimalPipe, FormsModule, PageHeaderComponent, StatusBadgeComponent, IconComponent],
  templateUrl: './employee-list.component.html'
})
export class EmployeeListComponent implements OnInit {
  private hr = inject(HrService);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);

  employees: EmployeeDTO[] = [];
  loading = true;
  refreshing = false;
  error = false;
  exporting: 'csv' | 'payroll' | null = null;

  searchTerm = '';
  sortColumn: SortColumn = 'name';
  sortDirection: 'asc' | 'desc' = 'asc';
  pageSize = 25;
  currentPage = 0; // 0-based like Spring's Pageable
  totalElements = 0;
  totalPages = 1;

  /** Debounced search: one request when the user stops typing. */
  private search$ = new Subject<void>();

  readonly columns: { key: SortColumn; label: string; right?: boolean }[] = [
    { key: 'name', label: 'Name' },
    { key: 'title', label: 'Title' },
    { key: 'department', label: 'Team' },
    { key: 'employeeStatus', label: 'Status' },
    { key: 'salary', label: 'Salary', right: true },
    { key: 'startDate', label: 'Start date' },
  ];

  ngOnInit(): void {
    this.search$.pipe(
      debounceTime(300),
      switchMap(() => {
        this.currentPage = 0;
        this.refreshing = true;
        return this.fetch();
      }),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({ next: p => this.show(p), error: () => this.fail() });
    this.load();
  }

  private fetch(page = this.currentPage, size = this.pageSize) {
    return this.hr.getEmployeesPaged(page, size, this.searchTerm, this.sortColumn, this.sortDirection);
  }

  private show(page: PageResponse<EmployeeDTO>): void {
    this.employees = page.content;
    this.totalElements = page.totalElements;
    this.totalPages = Math.max(1, page.totalPages);
    this.loading = this.refreshing = this.error = false;
  }

  private fail(): void {
    this.error = true;
    this.loading = this.refreshing = false;
  }

  load(): void {
    if (this.employees.length) this.refreshing = true; else this.loading = true;
    this.fetch().subscribe({ next: p => this.show(p), error: () => this.fail() });
  }

  onSearch(): void {
    this.search$.next();
  }

  sort(column: SortColumn): void {
    this.sortDirection = this.sortColumn === column && this.sortDirection === 'asc' ? 'desc' : 'asc';
    this.sortColumn = column;
    this.currentPage = 0;
    this.load();
  }

  goTo(page: number): void {
    if (page < 0 || page >= this.totalPages) return;
    this.currentPage = page;
    this.load();
  }

  open(e: EmployeeDTO): void {
    this.router.navigate(['/dashboard/employee', e.employeeId]);
  }

  /** Every employee matching the current search, as CSV (the API serves 200 per page). */
  exportCsv(): void {
    const size = 200;
    this.exporting = 'csv';
    this.fetch(0, size).pipe(
      switchMap(first => {
        const rest = Array.from({ length: Math.max(0, first.totalPages - 1) }, (_, i) => this.fetch(i + 1, size));
        return rest.length ? forkJoin(rest).pipe(map(pages => [first, ...pages])) : of([first]);
      })
    ).subscribe({
      next: pages => {
        const rows = pages.flatMap(p => p.content) as unknown as Record<string, unknown>[];
        saveFile(toCsv(rows, EXPORT_COLUMNS), 'employees.csv');
        this.exporting = null;
      },
      error: () => this.exporting = null
    });
  }

  exportPayroll(): void {
    this.exporting = 'payroll';
    this.hr.exportPayroll().subscribe({
      next: blob => {
        saveFile(blob, `payroll-${new Date().toISOString().slice(0, 7)}.csv`);
        this.exporting = null;
      },
      error: () => this.exporting = null
    });
  }
}

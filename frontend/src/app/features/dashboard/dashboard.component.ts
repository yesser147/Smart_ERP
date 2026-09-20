import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, NavigationEnd, Router, RouterLink, RouterOutlet } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';

import { HrDashboardComponent } from './hr-dashboard/hr-dashboard.component';
import { AdminDashboardComponent } from './admin-dashboard/admin-dashboard.component';
import { EmployeeDashboardComponent } from './employee-dashboard/employee-dashboard.component';
import { AiAssistantComponent } from '../ai-assistant/ai-assistant.component';
import { HrBudgetAdvisorComponent } from './hr-budget-advisor/hr-budget-advisor.component';
import { HrRetentionComponent } from './hr-retention/hr-retention.component';
import { DepartmentListComponent } from './department-list/department-list.component';

const SIDEBAR_COLLAPSED_KEY = 'nexus_erp_sidebar_collapsed';

const ROLE_LABELS: Record<string, string> = {
  ROLE_HR_MANAGER: 'HR Manager',
  ROLE_ADMIN: 'Admin',
  ROLE_EMPLOYEE: 'Employee',
  ROLE_MANAGER: 'Manager',
};

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterOutlet,
    HrDashboardComponent,
    AdminDashboardComponent,
    EmployeeDashboardComponent,
    AiAssistantComponent,
    HrBudgetAdvisorComponent,
    HrRetentionComponent,
    DepartmentListComponent
  ],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit {
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  userInfo: any = null;
  activeMenu: string = 'overview'; // Tracks which sidebar menu is clicked
  sidebarCollapsed = false;

  /** true while a child page (applicant detail, hire form...) is open */
  childActive = !!this.route.snapshot.firstChild;

  constructor() {
    this.router.events
      .pipe(filter(e => e instanceof NavigationEnd), takeUntilDestroyed())
      .subscribe(() => { this.childActive = !!this.route.snapshot.firstChild; });
  }

  ngOnInit() {
    this.userInfo = {
      email: 'hr@smarterp.com',
      role: 'ROLE_HR_MANAGER'
      // TODO: once login returns firstName/lastName, add them here too
    };

    try {
      this.sidebarCollapsed = localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === 'true';
    } catch {
      this.sidebarCollapsed = false;
    }
  }

  /** Sidebar click: select the tab, and leave the child page if one is open. */
  selectMenu(menu: string): void {
    this.activeMenu = menu;
    if (this.childActive) this.router.navigate(['/dashboard']);
  }

  toggleSidebar(): void {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    try {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(this.sidebarCollapsed));
    } catch {
      /* ignore quota / private mode errors */
    }
  }

  get roleLabel(): string {
    const role = this.userInfo?.role as string | undefined;
    return (role && ROLE_LABELS[role]) || role || '';
  }

  get displayName(): string {
    const info = this.userInfo;
    const first = info?.firstName ?? info?.first_name;
    const last = info?.lastName ?? info?.last_name;
    const full = `${first ?? ''} ${last ?? ''}`.trim();
    if (full) return full;
    const email = (info?.email as string) || '';
    return email.includes('@') ? email.split('@')[0] : email;
  }

  isGroupActive(keys: string[]): boolean {
    return keys.includes(this.activeMenu);
  }

  logout() {
    console.log('Logout clicked');
  }
}
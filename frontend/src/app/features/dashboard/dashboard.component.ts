import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { HrDashboardComponent } from './hr-dashboard/hr-dashboard.component';
import { AdminDashboardComponent } from './admin-dashboard/admin-dashboard.component';
import { EmployeeDashboardComponent } from './employee-dashboard/employee-dashboard.component';
import { AiAssistantComponent } from '../ai-assistant/ai-assistant.component';
import { HrBudgetAdvisorComponent } from './hr-budget-advisor/hr-budget-advisor.component';
import { HrRetentionComponent } from './hr-retention/hr-retention.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    HrDashboardComponent,
    AdminDashboardComponent,
    EmployeeDashboardComponent,
    AiAssistantComponent,
    HrBudgetAdvisorComponent, // <--- Added
    HrRetentionComponent
  ],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit {
  
  userInfo: any = null; 
  activeMenu: string = 'overview'; // Tracks which sidebar menu is clicked

  ngOnInit() {
    this.userInfo = {
      email: 'hr@smarterp.com',
      role: 'ROLE_HR_MANAGER' 
    };
  }

  logout() {
    console.log('Logout clicked');
  }
}
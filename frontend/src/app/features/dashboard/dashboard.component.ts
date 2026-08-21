import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router'; // Required for routerLink in HTML
import { AuthService } from '../../core/services/auth.service'; // Adjust path if needed

// 1. IMPORT YOUR NEW COMPONENTS HERE
import { HrDashboardComponent } from './hr-dashboard/hr-dashboard.component';
import { AdminDashboardComponent } from './admin-dashboard/admin-dashboard.component';
import { EmployeeDashboardComponent } from './employee-dashboard/employee-dashboard.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  // 2. ADD THEM TO THE IMPORTS ARRAY HERE
  imports: [
    CommonModule,
    RouterLink,
    HrDashboardComponent,
    AdminDashboardComponent,
    EmployeeDashboardComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss' // Change to .css if you use CSS
})
export class DashboardComponent implements OnInit {
  
  // Example properties based on your HTML
  userInfo: any = null; 

  ngOnInit() {
    // Mock user for now so you can see the HR Dashboard
    // Replace this with your actual AuthService call later
    this.userInfo = {
      email: 'hr@smarterp.com',
      role: 'ROLE_HR_MANAGER' 
    };
  }

  logout() {
    console.log('Logout clicked');
    // this.authService.logout();
  }
}
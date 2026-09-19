import { Routes } from '@angular/router';

export const DASHBOARD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./dashboard.component').then(m => m.DashboardComponent)
  },
   {
    path: 'register',
    loadComponent: () => import('../auth/register/register.component').then(m => m.RegisterComponent)
  },
    {
    path: 'apply',
    loadComponent: () => import('./job-application-form/job-application-form.component').then(m => m.JobApplicationFormComponent)
  },
  {
    path: 'employee/:id',
    loadComponent: () => import('./employee-detail/employee-detail.component').then(m => m.EmployeeDetailComponent)
  },
  {
    path: 'departments/:id',
    loadComponent: () => import('./department-detail/department-detail.component').then(m => m.DepartmentDetailComponent)
  },
  {
  path: 'department-type/:type',
  loadComponent: () => import('./department-type-detail/department-type-detail.component').then(m => m.DepartmentTypeDetailComponent)
},
{ path: 'applicant/:id', loadComponent: () => import('./applicant-detail/applicant-detail.component').then(m => m.ApplicantDetailComponent) },

];
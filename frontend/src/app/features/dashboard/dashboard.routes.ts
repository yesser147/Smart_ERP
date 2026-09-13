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

];
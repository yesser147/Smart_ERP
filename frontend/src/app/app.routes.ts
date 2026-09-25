import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },
  {
    path: 'careers',
    title: 'Careers - Nexus',
    loadComponent: () => import('./features/careers/careers.component').then(m => m.CareersComponent)
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    title: 'Nexus ERP',
    loadChildren: () => import('./layout/shell/shell.routes').then(m => m.SHELL_ROUTES)
  },
  { path: '**', redirectTo: 'dashboard' }
];

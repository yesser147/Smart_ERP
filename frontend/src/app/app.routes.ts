import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { guestGuard } from './core/guards/guest.guard';

export const routes: Routes = [
  {
    // public home: careers or sign-in (signed-in users go straight to their dashboard)
    path: '',
    pathMatch: 'full',
    canActivate: [guestGuard],
    title: 'Nexus',
    loadComponent: () => import('./features/landing/landing.component').then(m => m.LandingComponent)
  },
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
  { path: '**', redirectTo: '' }
];

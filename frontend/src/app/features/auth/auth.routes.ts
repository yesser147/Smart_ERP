import { Routes } from '@angular/router';
import { guestGuard } from '../../core/guards/guest.guard';

export const AUTH_ROUTES: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'forgot-password',
    canActivate: [guestGuard],
    loadComponent: () => import('./forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
  },
  {
    // opened from the e-mail link, so it works even with another session open
    path: 'set-password',
    loadComponent: () => import('./set-password/set-password.component').then(m => m.SetPasswordComponent)
  },
  { path: '', pathMatch: 'full', redirectTo: 'login' }
];

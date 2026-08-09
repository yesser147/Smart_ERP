import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { TokenService } from '../services/token.service';

export const guestGuard: CanActivateFn = (route, state) => {
  const tokenService = inject(TokenService);
  const router = inject(Router);

  // If the user already has a token, they shouldn't be on the auth pages
  if (tokenService.hasToken()) {
    router.navigate(['/dashboard']);
    return false;
  }

  // If they don't have a token, allow them to view the login/register page
  return true;
};
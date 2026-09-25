import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { TokenService } from '../services/token.service';

/** Keeps signed-in users away from the login pages. */
export const guestGuard: CanActivateFn = () => {
  const tokenService = inject(TokenService);
  const router = inject(Router);
  return tokenService.isTokenValid() ? router.createUrlTree(['/dashboard']) : true;
};

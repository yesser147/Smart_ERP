import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { TokenService } from '../services/token.service';

export const authGuard: CanActivateFn = (route, state) => {
  const tokenService = inject(TokenService);
  const router = inject(Router);

  if (tokenService.isTokenValid()) {
    return true;
  }
  // missing or expired token: start from a clean session
  tokenService.clearAuthData();
  return router.createUrlTree(['/auth/login'], { queryParams: { returnUrl: state.url } });
};

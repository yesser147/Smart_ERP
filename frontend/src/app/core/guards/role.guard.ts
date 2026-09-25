import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { TokenService } from '../services/token.service';
import { RoleName } from '../models/auth.model';

export const HR_ROLES: RoleName[] = ['ROLE_ADMIN', 'ROLE_HR_MANAGER', 'ROLE_MANAGER'];

/** Opens the route only for the given roles; the others go to their home page. */
export const roleGuard = (roles: RoleName[]): CanActivateFn => () => {
  const tokenService = inject(TokenService);
  const router = inject(Router);
  return tokenService.hasAnyRole(roles) ? true : router.createUrlTree(['/dashboard']);
};

/** /dashboard -> the right home page for the role. */
export const homeRedirectGuard: CanActivateFn = () => {
  const tokenService = inject(TokenService);
  const router = inject(Router);
  return router.createUrlTree([tokenService.hasAnyRole(HR_ROLES) ? '/dashboard/overview' : '/dashboard/me']);
};

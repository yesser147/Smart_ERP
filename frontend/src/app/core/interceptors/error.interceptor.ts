import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { TokenService } from '../services/token.service';

/** 401 = the session is gone (expired / revoked token): back to the login page.
 *  403 only means "not allowed for your role" and must not log the user out. */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const tokenService = inject(TokenService);

  return next(req).pipe(
    catchError((error) => {
      if (error.status === 401 && tokenService.getToken()) {
        tokenService.clearAuthData();
        router.navigate(['/auth/login'], { queryParams: { returnUrl: router.url } });
      }
      return throwError(() => error);
    })
  );
};

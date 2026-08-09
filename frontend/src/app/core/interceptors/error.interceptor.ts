import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { TokenService } from '../services/token.service';
//automatically attaches Authorization: Bearer <JWT> to every outgoing HTTP request.
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const tokenService = inject(TokenService);

  return next(req).pipe(
    catchError((error) => {
      if (error.status === 401 || error.status === 403) {
        tokenService.clearAuthData();
        router.navigate(['/auth/login']);
      }
      return throwError(() => error);
    })
  );
};
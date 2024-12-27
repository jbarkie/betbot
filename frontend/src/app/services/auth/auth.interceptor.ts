import {
  HttpErrorResponse,
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpRequest,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { catchError, throwError } from 'rxjs';
import { ToastService } from '../../components/toast/toast.service';
import { ApplicationState } from '../../state';
import { authActions } from '../../state/auth/auth.actions';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (
  request: HttpRequest<unknown>,
  next: HttpHandlerFn
) => {
  const authService = inject(AuthService);
  const store = inject(Store<ApplicationState>);
  const toastService = inject(ToastService);

  console.log('intercepting request');
  const token = authService.getToken();
  if (token) {
    request = request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(request).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        store.dispatch(authActions.logout());
        store.dispatch(authActions.showLoginModal());
        toastService.showError('Session expired. Please log in again.');
      }
      return throwError(() => error);
    })
  );
};

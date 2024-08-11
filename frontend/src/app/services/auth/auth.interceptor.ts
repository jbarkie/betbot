import {
    HTTP_INTERCEPTORS,
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import { Injectable, Provider } from '@angular/core';
import { AuthService } from './auth.service';
import { ApplicationState } from '../../state';
import { Store } from '@ngrx/store';
import { Router } from '@angular/router';
import { catchError, Observable, throwError } from 'rxjs';
import { authActions } from '../../state/auth/auth.actions';
import { ToastService } from '../../components/toast/toast.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(
    private authService: AuthService,
    private store: Store<ApplicationState>,
    private router: Router,
    private toastService: ToastService
  ) {}

  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler
  ): Observable<HttpEvent<unknown>> {
    console.log('intercepting request');
    const token = this.authService.getToken();
    if (token) {
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      });
    }
    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          this.store.dispatch(authActions.logout());
          this.toastService.showError('Session expired. Please log in again.');
          this.router.navigate(['/login']);
        }
        return throwError(() => error);
      })
    );
  }
}

export const authInterceptProvider: Provider = {
    provide: HTTP_INTERCEPTORS, 
    useClass: AuthInterceptor,
    multi: true
}

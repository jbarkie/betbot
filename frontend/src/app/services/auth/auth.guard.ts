import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { ToastService } from '../../components/toast/toast.service';
import { Store } from '@ngrx/store';
import { ApplicationState } from '../../state';
import { map, take } from 'rxjs/operators';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const toastService = inject(ToastService);
  const store = inject(Store<ApplicationState>);

  return store
    .select((state) => state.auth.isAuthenticated)
    .pipe(
      take(1),
      map((isAuthenticated) => {
        if (isAuthenticated && authService.isTokenValid()) {
          return true;
        } else {
          toastService.showError('You must be logged in to access this page.');
          return false;
        }
      })
    );
};

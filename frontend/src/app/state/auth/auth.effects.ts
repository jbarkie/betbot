import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { AuthService } from '../../services/auth/auth.service';
import { authActions } from './auth.actions';
import { of, switchMap } from 'rxjs';

@Injectable()
export class AuthEffects {
  initializeAuth$ = createEffect(() =>
    this.actions$.pipe(
      ofType(authActions.initializeAuth),
      switchMap(() => {
        const token = this.authService.getToken();
        if (token && this.authService.isTokenValid()) {
          return of(authActions.initializeAuthSuccess({ token }));
        } else {
          this.authService.removeToken();
          return of(authActions.initializeAuthFailure());
        }
      })
    )
  );

  constructor(private actions$: Actions, private authService: AuthService) {}
}

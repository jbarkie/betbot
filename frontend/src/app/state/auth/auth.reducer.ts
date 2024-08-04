import { createReducer, on } from '@ngrx/store';
import { authActions } from './auth.actions';

export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  error: string | null;
}

export const initialAuthState: AuthState = {
  isAuthenticated: false,
  token: null,
  error: null,
};

export const authReducer = createReducer(
  initialAuthState,
  on(authActions.loginSuccess, (state, { token }) => ({
    ...state,
    isAuthenticated: true,
    token,
    error: null,
  })),
  on(authActions.loginFailure, (state, { error }) => ({
    ...state,
    isAuthenticated: false,
    token: null,
    error,
  })),
  on(authActions.logout, () => initialAuthState)
);

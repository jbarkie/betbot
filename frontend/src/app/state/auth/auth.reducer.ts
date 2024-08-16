import { createReducer, on } from '@ngrx/store';
import { authActions } from './auth.actions';

export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  error: string | null;
  showLoginModal: boolean;
}

export const initialAuthState: AuthState = {
  isAuthenticated: false,
  token: null,
  error: null,
  showLoginModal: false,
};

export const authReducer = createReducer(
  initialAuthState,
  on(authActions.initializeAuthSuccess, (state, { token }) => ({
    ...state,
    isAuthenticated: true,
    token,
    error: null,
    showLoginModal: false,
  })),
  on(authActions.initializeAuthFailure, (state) => ({
    ...state,
    isAuthenticated: false,
    token: null,
    error: null,
    showLoginModal: true
  })),
  on(authActions.registerSuccess, (state, { token }) => ({
    ...state,
    isAuthenticated: true,
    token,
    error: null,
    showLoginModal: false,
  })),
  on(authActions.registerFailure, (state, { error }) => ({
    ...state,
    isAuthenticated: false,
    token: null,
    error,
    showLoginModal: false,
  })),
  on(authActions.loginSuccess, (state, { token }) => ({
    ...state,
    isAuthenticated: true,
    token,
    error: null,
    showLoginModal: false,
  })),
  on(authActions.loginFailure, (state, { error }) => ({
    ...state,
    isAuthenticated: false,
    token: null,
    error,
    showLoginModal: true,
  })),
  on(authActions.logout, () => initialAuthState),
  on(authActions.showLoginModal, (state) => ({
    ...state,
    showLoginModal: true,
  })),
  on(authActions.hideLoginModal, (state) => ({
    ...state,
    showLoginModal: false,
  }))
);

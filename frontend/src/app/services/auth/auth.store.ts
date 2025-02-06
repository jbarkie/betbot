import { computed, inject } from '@angular/core';
import { signalStore, withComputed, withMethods, withState, patchState } from '@ngrx/signals';
import { AuthService } from '../../services/auth/auth.service';
import { RegistrationService } from '../../components/registration/registration.service';
import { LoginService } from '../../components/login/login.service';
import { LoginRequest, RegisterRequest } from '../../components/models';
import { firstValueFrom } from 'rxjs';
import { AuthState } from './models';

const initialState: AuthState = {
  isAuthenticated: false,
  token: null,
  error: null,
  shouldShowLoginModal: false,
};

export const AuthStore = signalStore(
  withState(initialState),
  withComputed((store) => ({
    hasError: computed(() => !!store.error()),
  })),
  withMethods((
    store, 
    authService = inject(AuthService), 
    registrationService = inject(RegistrationService),
    loginService = inject(LoginService),
) => ({
    async initializeAuth() {
      const token = authService.getToken();
      if (token && authService.isTokenValid()) {
        patchState(store, {
          isAuthenticated: true,
          token,
          error: null,
          shouldShowLoginModal: false,
        });
      } else {
        authService.removeToken();
        patchState(store, {
          isAuthenticated: false,
          token: null,
          error: null,
          shouldShowLoginModal: true,
        });
      }
    },

    async register(request: RegisterRequest) {
      try {
        const response = await firstValueFrom(registrationService.register(request));
        const token = response.access_token;
        authService.setToken(token);

        patchState(store, {
          isAuthenticated: true,
          token,
          error: null,
          shouldShowLoginModal: false,
        });
      } catch (error) {
        patchState(store, {
          isAuthenticated: false,
          token: null,
          error: error instanceof Error ? error.message : 'Registration failed',
          shouldShowLoginModal: false,
        });
      }
    },

    async login(request: LoginRequest) {
      try {
        const response = await firstValueFrom(loginService.login(request));
        const token = response.access_token;
        authService.setToken(token);

        patchState(store, {
          isAuthenticated: true,
          token,
          error: null,
          shouldShowLoginModal: false,
        });
      } catch (error) {
        patchState(store, {
          isAuthenticated: false,
          token: null,
          error: error instanceof Error ? error.message : 'Login failed',
          shouldShowLoginModal: true,
        });
      }
    },

    logout() {
      authService.removeToken();
      patchState(store, initialState);
    },

    showLoginModal() {
      patchState(store, { shouldShowLoginModal: true });
    },

    hideLoginModal() {
      patchState(store, { shouldShowLoginModal: false });
    },
  }))
);
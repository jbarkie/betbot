import { computed, inject } from '@angular/core';
import { signalStore, withComputed, withMethods, withState, patchState } from '@ngrx/signals';
import { AuthService } from '../../services/auth/auth.service';
import { RegistrationService } from '../../components/registration/registration.service';
import { LoginService } from '../../components/login/login.service';
import { LoginRequest, RegisterRequest } from '../../components/models';
import { firstValueFrom } from 'rxjs';

export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  error: string | null;
  showLoginModal: boolean;
}

const initialState: AuthState = {
  isAuthenticated: false,
  token: null,
  error: null,
  showLoginModal: false,
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
          showLoginModal: false,
        });
      } else {
        authService.removeToken();
        patchState(store, {
          isAuthenticated: false,
          token: null,
          error: null,
          showLoginModal: true,
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
          showLoginModal: false,
        });
      } catch (error) {
        patchState(store, {
          isAuthenticated: false,
          token: null,
          error: error instanceof Error ? error.message : 'Registration failed',
          showLoginModal: false,
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
          showLoginModal: false,
        });
      } catch (error) {
        patchState(store, {
          isAuthenticated: false,
          token: null,
          error: error instanceof Error ? error.message : 'Login failed',
          showLoginModal: true,
        });
      }
    },

    logout() {
      authService.removeToken();
      patchState(store, initialState);
    },

    showLoginModal() {
      patchState(store, { showLoginModal: true });
    },

    hideLoginModal() {
      patchState(store, { showLoginModal: false });
    },
  }))
);
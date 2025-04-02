import { inject } from '@angular/core';
import { CanActivateFn } from '@angular/router';
import { ToastService } from '../../components/toast/toast.service';
import { AuthStore } from './auth.store';

export const authGuard: CanActivateFn = (_route, _state) => {
  const authStore = inject(AuthStore);
  const toastService = inject(ToastService);

  const isAuthenticated = authStore.isAuthenticated();
  const token = authStore.token();

  if (isAuthenticated && token) {
    return true;
  } else {
    toastService.showError('You must be logged in to access this page.');
    authStore.showLoginModal();
    return false;
  }
};

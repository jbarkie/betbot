import { computed, inject } from '@angular/core';
import {
  signalStore,
  withComputed,
  withMethods,
  withState,
  patchState,
} from '@ngrx/signals';
import { SettingsService } from './settings.service';
import { ToastService } from '../toast/toast.service';
import { SettingsRequest } from '../models';
import { firstValueFrom } from 'rxjs';

interface SettingsState {
  isLoading: boolean;
  error: string | null;
  settings: SettingsRequest | null;
}

const initialState: SettingsState = {
  isLoading: false,
  error: null,
  settings: null,
};

export const SettingsStore = signalStore(
  withState(initialState),
  withComputed((store) => ({
    hasError: computed(() => !!store.error()),
  })),
  withMethods(
    (
      store,
      settingsService = inject(SettingsService),
      toastService = inject(ToastService)
    ) => ({
      async loadSettings() {
        try {
          patchState(store, { isLoading: true, error: null });
          const settings = await firstValueFrom(settingsService.getSettings());
          patchState(store, { settings, isLoading: false });
        } catch (error) {
          patchState(store, {
            error:
              error instanceof Error
                ? error.message
                : 'Failed to load settings',
            isLoading: false,
          });
          toastService.showError('Failed to load settings');
        }
      },
      async updateSettings(request: SettingsRequest) {
        try {
          patchState(store, { isLoading: true, error: null });
          await firstValueFrom(settingsService.updateSettings(request));
          patchState(store, { settings: request, isLoading: false });
          toastService.showSuccess('Settings updated successfully');
        } catch (error) {
          patchState(store, {
            error:
              error instanceof Error
                ? error.message
                : 'Failed to update settings',
            isLoading: false,
          });
          toastService.showError('Failed to update settings');
        }
      },
    })
  )
);

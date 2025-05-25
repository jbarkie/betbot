import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { SettingsStore } from './settings.store';
import { SettingsService } from './settings.service';
import { ToastService } from '../toast/toast.service';
import { SettingsRequest } from '../models';

describe('SettingsStore', () => {
  let store: InstanceType<typeof SettingsStore>;
  let settingsService: { getSettings: jest.Mock; updateSettings: jest.Mock };
  let toastService: { showError: jest.Mock; showSuccess: jest.Mock };

  beforeEach(() => {
    settingsService = {
      getSettings: jest.fn(),
      updateSettings: jest.fn(),
    };

    toastService = {
      showError: jest.fn(),
      showSuccess: jest.fn(),
    };

    TestBed.configureTestingModule({
      imports: [],
      providers: [
        SettingsStore,
        { provide: SettingsService, useValue: settingsService },
        { provide: ToastService, useValue: toastService },
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    store = TestBed.inject(SettingsStore);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should create the store', () => {
    expect(store).toBeTruthy();
  });

  describe('updateSettings', () => {
    it('should update settings when update succeeds', async () => {
      const mockSettingsRequest: SettingsRequest = {
        email: 'updated@example.com',
        username: 'updateduser',
        password: 'newpassword123',
        email_notifications_enabled: false,
      };

      settingsService.updateSettings.mockReturnValue(of({}));

      await store.updateSettings(mockSettingsRequest);

      expect(settingsService.updateSettings).toHaveBeenCalledWith(
        mockSettingsRequest
      );
      expect(store.settings()).toEqual(mockSettingsRequest);
      expect(store.isLoading()).toEqual(false);
      expect(store.error()).toBeNull();
      expect(toastService.showSuccess).toHaveBeenCalledWith(
        'Settings updated successfully'
      );
      expect(toastService.showError).not.toHaveBeenCalled();
    });

    it('should set error when update fails', async () => {
      const mockSettingsRequest: SettingsRequest = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'password123',
        email_notifications_enabled: true,
      };
      const mockError = new Error('Failed to update settings');

      settingsService.updateSettings.mockReturnValue(
        throwError(() => mockError)
      );

      await store.updateSettings(mockSettingsRequest);

      expect(settingsService.updateSettings).toHaveBeenCalledWith(
        mockSettingsRequest
      );
      expect(store.settings()).toBeNull(); // Settings remain null as update failed
      expect(store.isLoading()).toEqual(false);
      expect(store.error()).toEqual(mockError.message);
      expect(toastService.showSuccess).not.toHaveBeenCalled();
      expect(toastService.showError).toHaveBeenCalledWith(
        'Failed to update settings'
      );
    });

    it('should maintain previous settings if update fails', async () => {
      // First load some initial settings
      const initialSettings: SettingsRequest = {
        email: 'initial@example.com',
        username: 'initialuser',
        password: 'initialpass',
        email_notifications_enabled: true,
      };
      settingsService.getSettings.mockReturnValue(of(initialSettings));
      await store.loadSettings();

      // Then attempt to update with new settings but fail
      const updatedSettings: SettingsRequest = {
        email: 'updated@example.com',
        username: 'updateduser',
        password: 'updatedpass',
        email_notifications_enabled: false,
      };
      const mockError = new Error('Failed to update settings');
      settingsService.updateSettings.mockReturnValue(
        throwError(() => mockError)
      );

      await store.updateSettings(updatedSettings);

      // Verify initial settings are preserved
      expect(store.settings()).toEqual(initialSettings);
      expect(store.isLoading()).toEqual(false);
      expect(store.error()).toEqual(mockError.message);
      expect(toastService.showError).toHaveBeenCalledWith(
        'Failed to update settings'
      );
    });
  });

  describe('loadSettings', () => {
    it('should set settings when load succeeds', async () => {
      const mockSettings: SettingsRequest = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'password123',
        email_notifications_enabled: true,
      };

      settingsService.getSettings.mockReturnValue(of(mockSettings));

      await store.loadSettings();

      expect(settingsService.getSettings).toHaveBeenCalled();
      expect(store.settings()).toEqual(mockSettings);
      expect(store.isLoading()).toEqual(false);
      expect(store.error()).toBeNull();
      expect(toastService.showError).not.toHaveBeenCalled();
    });

    it('should set error when load fails', async () => {
      const mockError = new Error('Failed to load settings');

      settingsService.getSettings.mockReturnValue(throwError(() => mockError));

      await store.loadSettings();

      expect(settingsService.getSettings).toHaveBeenCalled();
      expect(store.settings()).toBeNull();
      expect(store.isLoading()).toEqual(false);
      expect(store.error()).toEqual(mockError.message);
      expect(toastService.showError).toHaveBeenCalledWith(
        'Failed to load settings'
      );
    });
  });

  describe('computed selectors', () => {
    it('should return correct value for hasError', async () => {
      // Initial state - no error
      expect(store.hasError()).toEqual(false);

      // Set an error by triggering the error path in loadSettings
      const mockError = new Error('Test error');
      settingsService.getSettings.mockReturnValue(throwError(() => mockError));

      // This will set the error state
      await store.loadSettings();

      // Now hasError should be true
      expect(store.hasError()).toEqual(true);
    });
  });
});

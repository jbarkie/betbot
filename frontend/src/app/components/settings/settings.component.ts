import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ThemeToggleComponent } from './theme-toggle/theme-toggle.component';
import { SettingsStore } from './settings.store';
import { SettingsRequest } from '../models';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ThemeToggleComponent],
  template: `
    <div class="container mx-auto p-4">
      <form [formGroup]="settingsForm" (ngSubmit)="onSubmit()">
        <!-- Account Settings Section -->
        <div class="card bg-base-100 shadow-xl mb-6">
          <div class="card-body">
            <h2 class="card-title text-xl mb-4">Account Settings</h2>
            <div class="space-y-4">
              <div class="form-control">
                <label class="label">
                  <span class="label-text">Email</span>
                </label>
                <input
                  type="email"
                  class="input input-bordered w-full max-w-md"
                  formControlName="email"
                />
                <div *ngIf="isInvalid('email')" class="text-error mt-1">
                  <p *ngIf="settingsForm.get('email')?.hasError('email')">
                    Please enter a valid email address.
                  </p>
                </div>
              </div>
              <div class="form-control">
                <label class="label">
                  <span class="label-text">Username</span>
                </label>
                <input
                  type="text"
                  class="input input-bordered w-full max-w-md"
                  formControlName="username"
                />
              </div>
              <div class="form-control">
                <label class="label">
                  <span class="label-text">Password</span>
                </label>
                <input
                  type="password"
                  class="input input-bordered w-full max-w-md"
                  formControlName="password"
                />
                <div *ngIf="isInvalid('password')" class="text-error mt-1">
                  <p
                    *ngIf="settingsForm.get('password')?.hasError('minlength')"
                  >
                    Password must be at least 8 characters.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Preferences Section -->
        <div class="card bg-base-100 shadow-xl mb-6">
          <div class="card-body">
            <h2 class="card-title text-xl mb-4">Preferences</h2>
            <div class="space-y-4">
              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text">Enable Email Notifications</span>
                  <input
                    type="checkbox"
                    class="toggle"
                    formControlName="emailNotifications"
                  />
                </label>
              </div>
              <app-theme-toggle />
            </div>
          </div>
        </div>

        <!-- Save Button -->
        <div class="mt-6 flex justify-end">
          <button
            class="btn btn-primary"
            type="submit"
            [disabled]="settingsForm.invalid || settingsStore.isLoading()"
          >
            <span
              *ngIf="settingsStore.isLoading()"
              class="loading loading-spinner"
            ></span>
            Save Changes
          </button>
        </div>
      </form>
    </div>
  `,
  styles: [],
  providers: [SettingsStore],
})
export class SettingsComponent implements OnInit {
  settingsForm: FormGroup;
  private formBuilder = inject(FormBuilder);
  settingsStore = inject(SettingsStore);

  constructor() {
    this.settingsForm = this.formBuilder.group({
      email: ['', [Validators.email]],
      username: [''],
      password: ['', [Validators.minLength(8)]],
      emailNotifications: [false],
    });
  }

  ngOnInit() {
    this.loadSettings();
  }

  async loadSettings() {
    await this.settingsStore.loadSettings();
    if (this.settingsStore.settings()) {
      const settings = this.settingsStore.settings();
      this.settingsForm.patchValue({
        email: settings?.email,
        username: settings?.username,
        emailNotifications: settings?.email_notifications_enabled,
      });
    }
  }

  isInvalid(controlName: string): boolean {
    const control = this.settingsForm.get(controlName);
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  async onSubmit() {
    if (this.settingsForm.valid) {
      const request: SettingsRequest = {
        email: this.settingsForm.get('email')?.value,
        username: this.settingsForm.get('username')?.value,
        email_notifications_enabled:
          this.settingsForm.get('emailNotifications')?.value,
      };

      // Only include password if it was changed
      const password = this.settingsForm.get('password')?.value;
      if (password) {
        request.password = password;
      }

      await this.settingsStore.updateSettings(request);
    }
  }
}

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ThemeToggleComponent } from './theme-toggle/theme-toggle.component';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, ThemeToggleComponent],
  template: `
    <div class="container mx-auto p-4">
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
                [value]="email"
              />
            </div>
            <div class="form-control">
              <label class="label">
                <span class="label-text">Username</span>
              </label>
              <input
                type="text"
                class="input input-bordered w-full max-w-md"
                [value]="username"
              />
            </div>
            <div class="form-control">
              <label class="label">
                <span class="label-text">Password</span>
              </label>
              <input
                type="text"
                class="input input-bordered w-full max-w-md"
                [value]="password"
              />
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
                  [(ngModel)]="emailNotifications"
                />
              </label>
            </div>
            <app-theme-toggle />
          </div>
        </div>
      </div>

      <!-- Save Button -->
      <div class="mt-6 flex justify-end">
        <button class="btn btn-primary" (click)="saveSettings()">
          Save Changes
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        width: 100%;
      }
    `,
  ],
})
export class SettingsComponent {
  email = '';
  username = '';
  password = '';
  emailNotifications = false;

  saveSettings(): void {
    // TODO: Implement settings save functionality
    console.log('Saving settings...');
  }
}

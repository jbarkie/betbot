import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { PageHeaderComponent } from './components/page-header/page-header.component';
import { ToastComponent } from './components/toast/toast.component';
import { AuthStore } from './services/auth/auth.store';
import { ThemeService } from './services/theme/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, PageHeaderComponent, ToastComponent],
  template: `<div class="container mx-auto">
    <app-page-header />
    <main>
      <router-outlet />
    </main>
    <app-toast />
  </div>`,
  styles: [],
})
export class AppComponent {
  title = 'BetBot';
  private authStore = inject(AuthStore);
  private themeService = inject(ThemeService);

  constructor() {
    this.initializeApplication();
  }

  private async initializeApplication() {
    await this.authStore.initializeAuth();
    // Theme service will automatically initialize from localStorage or system preference
  }
}

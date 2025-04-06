import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { PageHeaderComponent } from './components/page-header/page-header.component';
import { ToastComponent } from './components/toast/toast.component';
import { AuthStore } from './services/auth/auth.store';
import { HomeComponent } from './components/home/home.component';
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, PageHeaderComponent, ToastComponent, HomeComponent],
  template: `<div class="container mx-auto">
    <app-page-header />
    <main>
      <router-outlet />
      <app-home />
    </main>
    <app-toast />
  </div>`,
  styles: [],
})
export class AppComponent {
  title = 'BetBot';
  private authStore = inject(AuthStore);

  constructor() {
    this.initializeApplication();
  }

  private async initializeApplication() {
    await this.authStore.initializeAuth();
  }
}

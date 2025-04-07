import { Component, inject } from '@angular/core';
import { AuthStore } from '../../services/auth/auth.store';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [],
  template: `
    <div class="hero min-h-screen">
      <div
        class="hero-content flex-col lg:flex-row-reverse w-full max-w-[1400px] gap-16 px-4 lg:px-8"
      >
        <div class="card flex-shrink-0 w-full lg:w-3/5 shadow-2xl">
          <div class="card-body items-center text-center p-8">
            <!-- Placeholder for image -->
            <div
              class="w-full aspect-video bg-base-200 rounded-lg flex items-center justify-center"
            >
              <img
                src="assets/img/betbot_home.png"
                class="w-full h-full rounded-lg"
                alt="BetBot Home Page Image"
              />
            </div>
          </div>
        </div>
        <div class="text-center lg:text-left lg:w-2/5">
          <h1 class="text-5xl lg:text-6xl font-bold leading-tight">
            Outsmart the Odds
          </h1>
          <p class="py-8 text-lg lg:text-xl leading-relaxed">
            Experience the next generation of betting analytics and insights.
            Our platform provides you with powerful tools and real-time data to
            make informed decisions and stay ahead of the game.
          </p>
          <button class="btn btn-primary btn-lg" (click)="showRegistration()">
            Login or Register Now!
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [],
})
export class HomeComponent {
  private authStore = inject(AuthStore);

  showRegistration() {
    this.authStore.showLoginModal();
  }
}

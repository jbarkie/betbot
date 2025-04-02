import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LoginComponent } from '../login/login.component';
import { CommonModule } from '@angular/common';
import { AuthStore } from '../../services/auth/auth.store';

@Component({
  selector: 'app-nav-bar',
  standalone: true,
  imports: [RouterLink, LoginComponent, CommonModule],
  template: `<div class="navbar bg-base-100">
      <div class="navbar-start">
        <div class="dropdown">
          <div tabindex="0" role="button" class="btn btn-ghost btn-circle">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h7"
              />
            </svg>
          </div>
          <ul
            tabindex="0"
            class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52"
          >
            <li><a routerLink="/">Home</a></li>
            <li>
              <details>
                <summary>Sports</summary>
                <ul class="p-2 bg-base-100 rounded-t-none">
                  <li><a routerLink="/nba">Basketball</a></li>
                  <li><a routerLink="/mlb">Baseball</a></li>
                  <li><a routerLink="/nfl">Football</a></li>
                  <li><a routerLink="/nhl">Hockey</a></li>
                </ul>
              </details>
            </li>
            <li><a routerLink="/about">About</a></li>
          </ul>
        </div>
      </div>
      <div class="navbar-center">
        <a routerLink="/" class="btn btn-ghost text-xl">BetBot</a>
      </div>
      <div class="navbar-end">
        <div class="form-control">
          <input
            type="text"
            placeholder="Search"
            class="input input-bordered w-24 md:w-auto"
          />
        </div>
        <div class="dropdown dropdown-end">
          <div
            tabindex="0"
            role="button"
            class="btn btn-ghost btn-circle avatar"
          >
            <div class="w-10 rounded-full">
              <img alt="Profile picture" src="assets/img/default_pfp.png" />
            </div>
          </div>
          <ul
            tabindex="0"
            class="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52"
          >
            <li *ngIf="!authStore.isAuthenticated()">
              <label for="login-modal" class="modal-button">Login</label>
            </li>
            <li *ngIf="authStore.isAuthenticated()">
              <a (click)="logout()">Logout</a>
            </li>
            <li><a>Settings</a></li>
          </ul>
        </div>
      </div>
    </div>
    <input
      type="checkbox"
      id="login-modal"
      class="modal-toggle"
      [checked]="authStore.isLoginModalDisplayed()"
      (change)="toggleLoginModal($event)"
    />
    <div class="modal">
      <app-login (closeModal)="closeLoginModal()"></app-login>
    </div> `,
  styles: [],
})
export class NavBarComponent {
  protected authStore = inject(AuthStore);

  openLoginModal() {
    this.authStore.showLoginModal();
  }

  closeLoginModal() {
    this.authStore.hideLoginModal();
  }

  toggleLoginModal(event: Event) {
    const isChecked = (event.target as HTMLInputElement).checked;
    if (isChecked) {
      this.openLoginModal();
    } else {
      this.closeLoginModal();
    }
  }

  logout() {
    this.authStore.logout();
  }
}

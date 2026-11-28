import { Component, ElementRef, effect, inject, untracked, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LoginComponent } from '../login/login.component';

import { AuthStore } from '../../services/auth/auth.store';

@Component({
  selector: 'app-nav-bar',
  standalone: true,
  imports: [RouterLink, LoginComponent],
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
              @if (!authStore.isAuthenticated()) {
                <li>
                  <button
                    type="button"
                    data-testid="open-login"
                    (click)="openLoginModal()"
                  >
                    Login
                  </button>
                </li>
              }
              @if (authStore.isAuthenticated()) {
                <li>
                  <a (click)="logout()">Logout</a>
                </li>
              }
              <li><a routerLink="/settings">Settings</a></li>
            </ul>
          </div>
        </div>
      </div>
      <!-- Native modal dialog: the browser traps focus, makes the page
           behind it inert, closes it on Escape and restores focus. -->
      <dialog
        #loginDialog
        class="modal"
        aria-labelledby="login-title"
        data-testid="login-dialog"
        (close)="closeLoginModal()"
      >
        <app-login (closeModal)="loginDialog.close()"></app-login>
        <form method="dialog" class="modal-backdrop">
          <button tabindex="-1">Close</button>
        </form>
      </dialog>`,
  styles: [],
})
export class NavBarComponent {
  protected authStore = inject(AuthStore);
  private loginDialog = viewChild.required<ElementRef<HTMLDialogElement>>('loginDialog');
  private loginForm = viewChild.required(LoginComponent);

  constructor() {
    // The auth store owns whether the login modal is shown (the auth guard
    // opens it too), so the dialog follows the store.
    effect(() => {
      const dialog = this.loginDialog().nativeElement;
      const shouldShow = this.authStore.isLoginModalDisplayed();
      if (shouldShow && !dialog.open) {
        dialog.showModal();
        // Opening moves focus to the username field. A field still focused
        // from the last time blurs during that move and Angular marks it
        // touched, so clear that state now.
        untracked(() => this.loginForm().loginForm.markAsUntouched());
      } else if (!shouldShow && dialog.open) {
        dialog.close();
      }
    });
  }

  openLoginModal() {
    this.authStore.showLoginModal();
  }

  closeLoginModal() {
    // Clear typed credentials and validation state when the dialog closes.
    this.loginForm().loginForm.reset();
    this.authStore.hideLoginModal();
  }

  logout() {
    this.authStore.logout();
  }
}

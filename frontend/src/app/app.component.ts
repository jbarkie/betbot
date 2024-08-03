import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { PageHeaderComponent } from './components/page-header/page-header.component';
import { Store } from '@ngrx/store';
import { appActions } from './state/actions';
import { ToastComponent } from './components/toast/toast.component';

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
  constructor(store: Store) {
    store.dispatch(appActions.applicationStarted());
  }
}

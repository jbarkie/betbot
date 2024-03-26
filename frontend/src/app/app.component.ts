import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { PageHeaderComponent } from './components/page-header/page-header.component';
import { Store } from '@ngrx/store';
import { appActions } from './state/actions';


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, PageHeaderComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'BetBot';
  constructor(store: Store) {
    store.dispatch(appActions.applicationStarted());
  }
}

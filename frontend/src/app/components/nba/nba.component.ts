import { DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { GamesListComponent } from '../games-list/games-list.component';
import { Store } from '@ngrx/store';
import { nbaFeature } from './state';
import { NbaCommands } from './state/actions';

@Component({
  selector: 'app-nba',
  standalone: true,
  template: `<p class="text-center mb-2">
      NBA odds for {{ today | date : 'EEEE, MMMM d' }}:
    </p>
    <app-games-list [list]="games()" />`,
  styles: [],
  imports: [DatePipe, GamesListComponent],
})
export class NbaComponent {
  today: Date = new Date();
  constructor(private store: Store) {}
  games = this.store.selectSignal(nbaFeature.selectNbaGames);
}

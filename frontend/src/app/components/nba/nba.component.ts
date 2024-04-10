import { DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { GamesListComponent } from '../games-list/games-list.component';
import { Store } from '@ngrx/store';
import { nbaFeature } from './state';
import { NbaCommands } from './state/actions';

@Component({
  selector: 'app-nba',
  standalone: true,
  template: ` <div class="flex justify-center">
      <ul class="menu menu-vertical lg:menu-horizontal bg-base-200 rounded-box">
        <li><a>&lt;</a></li>
        <p class="text-center mt-2">
          NBA odds for {{ today | date : 'EEEE, MMMM d' }}:
        </p>
        <li><a>&gt;</a></li>
      </ul>
    </div>
    <app-games-list [list]="games()" />`,
  styles: [],
  imports: [DatePipe, GamesListComponent],
})
export class NbaComponent {
  today: Date = new Date();
  constructor(private store: Store) {}
  games = this.store.selectSignal(nbaFeature.selectNbaGames);
}

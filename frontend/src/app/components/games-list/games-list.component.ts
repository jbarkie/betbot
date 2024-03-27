import { Component, inject, input } from '@angular/core';
import { Game } from '../models';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { GameComponent } from '../game/game.component';
import { Store } from '@ngrx/store';
import { nbaFeature } from '../nba/state';
import { NbaCommands } from '../nba/state/actions';

@Component({
  selector: 'app-games-list',
  standalone: true,
  template: `@if(loaded()) { @if(list().length === 0) {
    <app-alert-message message="No games found for today." />
    } @else { @for(item of list(); track item.id) {
    <app-game [game]="item" />
    } } } @else {
    <div class="loading-container">
      <span class="loading loading-bars loading-lg"></span>
    </div>
    }`,
  styles: [
    '.loading-container { display: flex; justify-content: center; margin-top: 48px }',
  ],
  imports: [AlertMessageComponent, GameComponent],
})
export class GamesListComponent {
  private store = inject(Store);
  list = input.required<Game[]>();
  loaded = this.store.selectSignal(nbaFeature.selectIsLoaded);
}

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
  templateUrl: './games-list.component.html',
  styleUrl: './games-list.component.css',
  imports: [AlertMessageComponent, GameComponent],
})
export class GamesListComponent {
  private store = inject(Store);
  list = input.required<Game[]>();
  loaded = this.store.selectSignal(nbaFeature.selectIsLoaded);
}

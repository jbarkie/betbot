import { Component, input } from '@angular/core';
import { Game } from '../models';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { GameComponent } from '../game/game.component';


@Component({
    selector: 'app-games-list',
    standalone: true,
    template: `
    @if (loaded() && !error()) {
      @if (list().length === 0) {
        <app-alert-message message="No games found for today." />
      }
      @if (list().length > 0) {
        @for (item of list(); track trackById($index, item)) {
          <app-game
            [game]="item"
          ></app-game>
        }
      }
    }
    @if (!loaded() && !error()) {
      <div class="loading-container">
        <span class="loading loading-bars loading-lg"></span>
      </div>
    }
    @if (error()) {
      <app-alert-message [message]="error() || 'An unexpected error occured while loading games.'" />
    }
    `,
    styles: [
        '.loading-container { display: flex; justify-content: center; margin-top: 48px }',
    ],
    imports: [AlertMessageComponent, GameComponent]
})
export class GamesListComponent {
  list = input.required<Game[]>();
  loaded = input.required<boolean>();
  error = input.required<string>();

  trackById(index: number, item: Game) {
    return item.id;
  }
}

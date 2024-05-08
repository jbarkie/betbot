import { Component, inject, input } from '@angular/core';
import { Game } from '../models';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { GameComponent } from '../game/game.component';
import { Store } from '@ngrx/store';
import { nbaFeature } from '../nba/state';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-games-list',
  standalone: true,
  template: `
    <ng-container *ngIf="loaded() && !error()">
      <ng-container *ngIf="list().length === 0">
        <app-alert-message message="No games found for today." />
      </ng-container>
      <ng-container *ngIf="list().length > 0">
        <app-game
          *ngFor="let item of list(); trackBy: trackById"
          [game]="item"
        ></app-game>
      </ng-container>
    </ng-container>
    <div *ngIf="!loaded() && !error()" class="loading-container">
      <span class="loading loading-bars loading-lg"></span>
    </div>
  `,
  styles: [
    '.loading-container { display: flex; justify-content: center; margin-top: 48px }',
  ],
  imports: [AlertMessageComponent, GameComponent, CommonModule],
})
export class GamesListComponent {
  private store = inject(Store);
  list = input.required<Game[]>();
  loaded = this.store.selectSignal(nbaFeature.selectIsLoaded);
  error = this.store.selectSignal(nbaFeature.selectError);

  trackById(index: number, item: Game) {
    return item.id;
  }
}

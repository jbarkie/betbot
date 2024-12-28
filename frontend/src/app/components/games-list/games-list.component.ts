import { Component, input } from '@angular/core';
import { Game } from '../models';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { GameComponent } from '../game/game.component';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-games-list',
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
    <app-alert-message *ngIf="error()" message="Error loading games." />
  `,
    styles: [
        '.loading-container { display: flex; justify-content: center; margin-top: 48px }',
    ],
    imports: [AlertMessageComponent, GameComponent, CommonModule]
})
export class GamesListComponent {
  list = input.required<Game[]>();
  loaded = input.required<boolean>();
  error = input.required<string>();

  trackById(index: number, item: Game) {
    return item.id;
  }
}

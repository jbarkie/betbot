import { Component, Input, Signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Store } from '@ngrx/store';
import { GamesListComponent } from '../games-list/games-list.component';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { Game } from '../models';

@Component({
  selector: 'app-sport-wrapper',
  standalone: true,
  template: `
    <div class="join flex justify-center my-5">
      <button
        class="join-item btn"
        (click)="previousDay()"
        [disabled]="isCurrentDate()"
      >
        «
      </button>
      <button class="join-item btn">
        {{ selectedDate | date : 'EEEE, MMMM d' }}
      </button>
      <button class="join-item btn" (click)="nextDay()">»</button>
    </div>
    <ng-container *ngIf="games()">
      <app-games-list [list]="games()"></app-games-list>
    </ng-container>
    <app-alert-message
      *ngIf="error()"
      [message]="'Error loading ' + sportName + ' games.'"
    />
  `,
  imports: [DatePipe, CommonModule, GamesListComponent, AlertMessageComponent],
})
export class SportWrapperComponent {
  @Input() sportName!: string;
  @Input() set gamesSelector(selector: (state: any) => Game[]) {
    this.games = this.store.selectSignal(selector);
  }
  @Input() set errorSelector(selector: (state: any) => boolean) {
    this.error = this.store.selectSignal(selector);
  }
  @Input() loadGamesAction!: any;

  selectedDate: Date = new Date();
  games: () => Game[] = () => [];
  error: () => boolean = () => false;

  constructor(private store: Store) {}

  previousDay() {
    this.selectedDate = new Date(
      this.selectedDate.getTime() - 24 * 60 * 60 * 1000
    );
    this.loadGames();
  }

  nextDay() {
    this.selectedDate = new Date(
      this.selectedDate.getTime() + 24 * 60 * 60 * 1000
    );
    this.loadGames();
  }

  isCurrentDate() {
    const today = new Date();
    return (
      this.selectedDate.getDate() === today.getDate() &&
      this.selectedDate.getMonth() === today.getMonth() &&
      this.selectedDate.getFullYear() === today.getFullYear()
    );
  }

  private loadGames() {
    this.store.dispatch(this.loadGamesAction({ date: this.selectedDate }));
  }
}

import { CommonModule, DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { GamesListComponent } from '../games-list/games-list.component';
import { Store } from '@ngrx/store';
import { nbaFeature } from './state';
import { NbaCommands } from './state/actions';
import { AlertMessageComponent } from '../alert-message/alert-message.component';

@Component({
  selector: 'app-nba',
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
      message="Error loading games."
    />
  `,
  styles: [],
  imports: [DatePipe, CommonModule, GamesListComponent, AlertMessageComponent],
})
export class NbaComponent {
  selectedDate: Date = new Date();
  constructor(private store: Store) {}
  games = this.store.selectSignal(nbaFeature.selectNbaGames);
  error = this.store.selectSignal(nbaFeature.selectError);

  previousDay() {
    this.selectedDate = new Date(
      this.selectedDate.getTime() - 24 * 60 * 60 * 1000
    );
    this.store.dispatch(NbaCommands.loadGames({ date: this.selectedDate }));
  }

  nextDay() {
    this.selectedDate = new Date(
      this.selectedDate.getTime() + 24 * 60 * 60 * 1000
    );
    this.store.dispatch(NbaCommands.loadGames({ date: this.selectedDate }));
  }

  isCurrentDate() {
    const today = new Date();
    return (
      this.selectedDate.getDate() === today.getDate() &&
      this.selectedDate.getMonth() === today.getMonth() &&
      this.selectedDate.getFullYear() === today.getFullYear()
    );
  }
}

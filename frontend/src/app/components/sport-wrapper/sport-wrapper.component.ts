import { CommonModule, DatePipe } from '@angular/common';
import { Component, inject, input, OnInit, Signal } from '@angular/core';
import { AuthStore } from '../../services/auth/auth.store';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { GamesListComponent } from '../games-list/games-list.component';
import { Game } from '../models';

@Component({
  selector: 'app-sport-wrapper',
  standalone: true,
  template: `
    <ng-container *ngIf="authStore.isAuthenticated(); else unauthenticated">
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
        <app-games-list
          [list]="games()"
          [loaded]="!isLoading()"
          [error]="error() || ''"
        ></app-games-list>
      </ng-container>
    </ng-container>
    <ng-template #unauthenticated>
      <app-alert-message message="You must be logged in to access this page." />
    </ng-template>
  `,
  imports: [DatePipe, CommonModule, GamesListComponent, AlertMessageComponent],
})
export class SportWrapperComponent implements OnInit {
  protected readonly authStore = inject(AuthStore);

  sportName = input.required<string>();
  games = input.required<Game[]>();
  isLoading = input.required<boolean>();
  error = input.required<string | null>();
  dateChange = input<(date: Date) => void>();

  selectedDate: Date = new Date();

  ngOnInit(): void {
    this.loadGames();
  }

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
    const dateChangeHandler = this.dateChange();
    if (dateChangeHandler) {
      dateChangeHandler(this.selectedDate);
    }
  }
}

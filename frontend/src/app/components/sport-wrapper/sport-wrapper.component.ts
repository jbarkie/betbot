import { Component, inject, Input, OnInit, Signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Store } from '@ngrx/store';
import { GamesListComponent } from '../games-list/games-list.component';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { Game } from '../models';
import { ApplicationState } from '../../state';

@Component({
    selector: 'app-sport-wrapper',
    standalone: true,
    template: `
    <ng-container *ngIf="isAuthenticated$ | async; else unauthenticated">
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
          [error]="error()  || ''"
        ></app-games-list>
      </ng-container>
    </ng-container>
    <ng-template #unauthenticated>
      <app-alert-message message="You must be logged in to access this page." />
    </ng-template>
  `,
    imports: [DatePipe, CommonModule, GamesListComponent, AlertMessageComponent]
})
export class SportWrapperComponent implements OnInit {
  private readonly store = inject(Store<ApplicationState>);

  @Input() sportName!: string;
  @Input() games!: Signal<Game[]>;
  @Input() isLoading!: Signal<boolean>;
  @Input() error!: Signal<string | null>;
  @Input() dateChange!: (date: Date) => void;
  
  selectedDate: Date = new Date();
  isAuthenticated$ = this.store.select((state) => state.auth.isAuthenticated);

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
    this.dateChange(this.selectedDate);
  }
}

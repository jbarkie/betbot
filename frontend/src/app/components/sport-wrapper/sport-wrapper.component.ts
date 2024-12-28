import { Component, Input, Signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Store } from '@ngrx/store';
import { GamesListComponent } from '../games-list/games-list.component';
import { AlertMessageComponent } from '../alert-message/alert-message.component';
import { Game } from '../models';
import { Observable } from 'rxjs';
import { ApplicationState } from '../../state';

@Component({
    selector: 'app-sport-wrapper',
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
          [loaded]="loaded()"
          [error]="error()"
        ></app-games-list>
      </ng-container>
    </ng-container>
    <ng-template #unauthenticated>
      <app-alert-message message="You must be logged in to access this page." />
    </ng-template>
  `,
    imports: [DatePipe, CommonModule, GamesListComponent, AlertMessageComponent]
})
export class SportWrapperComponent {
  @Input() sportName!: string;
  @Input() set gamesSelector(selector: (state: ApplicationState) => Game[]) {
    this.games = this.store.selectSignal(selector);
  }
  @Input() set errorSelector(selector: (state: ApplicationState) => string) {
    this.error = this.store.selectSignal(selector);
  }

  @Input() set loadedSelector(selector: (state: ApplicationState) => boolean) {
    this.loaded = this.store.selectSignal(selector);
  }

  @Input() loadGamesAction!: (props: { date: Date }) => {
    type: string;
    date: Date;
  };

  selectedDate: Date = new Date();
  games!: Signal<Game[]>;
  loaded!: Signal<boolean>;
  error!: Signal<string>;
  isAuthenticated$!: Observable<boolean>;

  constructor(private store: Store<ApplicationState>) {}

  ngOnInit() {
    this.isAuthenticated$ = this.store.select(
      (state) => state.auth.isAuthenticated
    );
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
    this.store.dispatch(this.loadGamesAction({ date: this.selectedDate }));
  }
}

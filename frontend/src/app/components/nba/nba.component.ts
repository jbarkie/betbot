import { DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { GamesListComponent } from '../games-list/games-list.component';
import { Game } from '../models';
import { Store } from '@ngrx/store';
import { nbaFeature } from './state';

@Component({
  selector: 'app-nba',
  standalone: true,
  templateUrl: './nba.component.html',
  styleUrl: './nba.component.css',
  imports: [DatePipe, GamesListComponent],
})
export class NbaComponent {
  today: Date = new Date();
  constructor(private store: Store) {}
  games = this.store.selectSignal(nbaFeature.selectNbaGames);
}

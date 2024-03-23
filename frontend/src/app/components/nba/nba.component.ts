import { DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { GamesListComponent } from '../games-list/games-list.component';
import { Game } from '../models';

@Component({
  selector: 'app-nba',
  standalone: true,
  templateUrl: './nba.component.html',
  styleUrl: './nba.component.css',
  imports: [DatePipe, GamesListComponent],
})
export class NbaComponent {
  today: Date = new Date();
  game1: Game = {
    id: '1',
    sport: 'NBA',
    awayTeam: 'LAL',
    homeTeam: 'BOS',
    date: '2024-03-25',
    odds: 'BOS -9.5',
  };
  games = [this.game1];
}

import { DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { GamesListComponent } from '../basketball/games-list/games-list.component';

@Component({
    selector: 'app-nba',
    standalone: true,
    templateUrl: './nba.component.html',
    styleUrl: './nba.component.css',
    imports: [DatePipe, GamesListComponent]
})
export class NbaComponent {
  today: Date = new Date();
}

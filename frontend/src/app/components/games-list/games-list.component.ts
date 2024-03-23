import { Component, input } from '@angular/core';
import { Game } from '../models';
import { AlertMessageComponent } from "../alert-message/alert-message.component";
import { GameComponent } from "../game/game.component";


@Component({
    selector: 'app-games-list',
    standalone: true,
    templateUrl: './games-list.component.html',
    styleUrl: './games-list.component.css',
    imports: [AlertMessageComponent, GameComponent]
})
export class GamesListComponent {
  list = input.required<Game[]>();
  
}

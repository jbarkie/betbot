import { Component, input } from '@angular/core';
import { Game } from '../models';

@Component({
  selector: 'app-game',
  standalone: true,
  imports: [],
  templateUrl: './game.component.html',
  styleUrl: './game.component.css'
})
export class GameComponent {
  game = input.required<Game>();
  
}

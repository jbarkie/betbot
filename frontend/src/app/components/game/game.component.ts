import { Component, input } from '@angular/core';
import { Game } from '../models';

@Component({
  selector: 'app-game',
  standalone: true,
  imports: [],
  schemas: [],
  template: ` 
  <div class="card card-side bg-base-100 shadow-xl mx-auto my-5 max-w-2xl">
  <figure>
    <img [src]="getImageSrc(game().homeTeam)" [alt]="game().homeTeam + ' logo'" class="w-28 mx-5" />
  </figure>
  <div class="card-body">
    <h2 class="card-title">{{ game().awayTeam }} &#64; <br/> {{ game().homeTeam }}</h2>
    @if(game().odds === {}) {
      <p class="text-md">No odds available</p>
    } @else {
      <p>{{ game().homeTeam }} ML: {{ game().odds['home'] }}</p>
      <p>{{ game().awayTeam }} ML: {{ game().odds['away'] }}</p>
    }
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Analyze</button>
    </div>
  </div>
  <figure>
    <img [src]="getImageSrc(game().awayTeam)" [alt]="game().awayTeam + ' logo'" class="w-28 mx-5" />
  </figure>
</div>`,
  styles: [],
})
export class GameComponent {
  game = input.required<Game>();

  getImageSrc(teamString: string) {
    const words = teamString.split(' ');
    const teamName = words[words.length - 1].toLowerCase();
    return `assets/img/${teamName}.png`;
  }
}

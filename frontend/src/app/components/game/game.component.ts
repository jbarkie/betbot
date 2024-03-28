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
    <img [src]="'assets/img/' + (game().awayTeam.split(' ').pop()?.toLowerCase()) + '.png'" alt="Away Team Logo" class="w-28 mx-5" />
  </figure>
  <div class="card-body">
    <h2 class="card-title">{{ game().awayTeam }} &#64; <br/> {{ game().homeTeam }}</h2>
    <p>{{ game().odds }}</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Analyze</button>
    </div>
  </div>
  <figure>
    <img [src]="'assets/img/' + (game().homeTeam.split(' ').pop()?.toLowerCase()) + '.png'" alt="Home Team Logo" class="w-28 mx-5" />
  </figure>
</div>`,
  styles: [],
})
export class GameComponent {
  game = input.required<Game>();
}

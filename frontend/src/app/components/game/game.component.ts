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
    <img [src]="getImageSrc(game().sport, game().awayTeam)" [alt]="game().awayTeam + ' logo'" class="w-28 mx-5" />
  </figure>
  <div class="card-body">
    <h2 class="card-title">{{ game().awayTeam }} &#64; <br/> {{ game().homeTeam }}</h2>
    @if (game().homeOdds === '' && game().awayOdds === '') {
      <p class="text-md">No odds available</p>
    }
    @else {
      <p>{{ game().awayTeam }} ML: {{ game().awayOdds }}</p>
      <p>{{ game().homeTeam }} ML: {{ game().homeOdds }}</p>
    }
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Analyze</button>
    </div>
  </div>
  <figure>
    <img [src]="getImageSrc(game().sport, game().homeTeam)" [alt]="game().homeTeam + ' logo'" class="w-28 mx-5" />
  </figure>
</div>`,
  styles: [],
})
export class GameComponent {
  game = input.required<Game>();

  getImageSrc(sport: string, teamString: string) {
    const teamName = this.normalizeTeamName(teamString);
    const extension = sport === 'MLB' ? 'svg' : 'png';
    return `assets/img/${sport.toLowerCase()}/${teamName}.${extension}`;
  }

  private normalizeTeamName(teamName: string): string {
    return teamName.toLowerCase()
      .replace(/\./g, '') 
      .replace(/\s+/g, '-'); 
  }
}

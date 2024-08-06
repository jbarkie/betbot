import { Component } from '@angular/core';
import { nbaFeature } from './state';
import { NbaCommands } from './state/actions';
import { SportWrapperComponent } from "../sport-wrapper/sport-wrapper.component";
import { Game } from '../models';

@Component({
  selector: 'app-nba',
  standalone: true,
  template: `
    <app-sport-wrapper
      sportName="NBA"
      [gamesSelector]="selectNbaGames"
      [errorSelector]="selectError"
      [loadGamesAction]="NbaCommands.loadGames"
    ></app-sport-wrapper>
  `,
  styles: [],
  imports: [SportWrapperComponent],
})
export class NbaComponent {
  selectNbaGames = (state: Game[]) => nbaFeature.selectNbaGames(state);
  selectError = (state: any) => nbaFeature.selectError(state);
  NbaCommands = NbaCommands;
}

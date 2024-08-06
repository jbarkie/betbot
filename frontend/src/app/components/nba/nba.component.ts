import { Component } from '@angular/core';
import { nbaFeature, NbaState } from './state';
import { NbaCommands } from './state/actions';
import { SportWrapperComponent } from "../sport-wrapper/sport-wrapper.component";

@Component({
  selector: 'app-nba',
  standalone: true,
  template: `
    <app-sport-wrapper
      sportName="NBA"
      [gamesSelector]="selectNbaGames"
      [errorSelector]="selectError"
      [loadGamesAction]="loadGames"
    ></app-sport-wrapper>
  `,
  styles: [],
  imports: [SportWrapperComponent],
})
export class NbaComponent {
  selectNbaGames = (state: { nba: NbaState }) => nbaFeature.selectNbaGames(state);
  selectError = (state: { nba: NbaState }) => nbaFeature.selectError(state);
  loadGames = NbaCommands.loadGames;
}

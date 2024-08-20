import { Component } from '@angular/core';
import { nbaFeature } from './state';
import { NBACommands } from './state/actions';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { ApplicationState } from '../../state';

@Component({
  selector: 'app-nba',
  standalone: true,
  template: `
    <app-sport-wrapper
      sportName="NBA"
      [gamesSelector]="selectNbaGames"
      [errorSelector]="selectError"
      [loadedSelector]="selectLoaded"
      [loadGamesAction]="loadGames"
    ></app-sport-wrapper>
  `,
  styles: [],
  imports: [SportWrapperComponent],
})
export class NbaComponent {
  selectNbaGames = (state: ApplicationState) =>
    nbaFeature.selectNbaGames(state);
  selectError = (state: ApplicationState) => nbaFeature.selectError(state);
  selectLoaded = (state: ApplicationState) => nbaFeature.selectIsLoaded(state);
  loadGames = NBACommands.loadGames;
}

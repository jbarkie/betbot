import { Component } from '@angular/core';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { ApplicationState } from '../../state';
import { nflFeature } from './state';
import { NFLCommands } from './state/actions';

@Component({
    selector: 'app-nfl',
    standalone: true,
    imports: [SportWrapperComponent],
    template: `
    <app-sport-wrapper
      sportName="NFL"
      [gamesSelector]="selectNflGames"
      [errorSelector]="selectError"
      [loadedSelector]="selectLoaded"
      [loadGamesAction]="loadGames"
    ></app-sport-wrapper>
  `,
    styles: ``
})
export class NflComponent {
  selectNflGames = (state: ApplicationState) =>
    nflFeature.selectNflGames(state);
  selectError = (state: ApplicationState) => nflFeature.selectError(state);
  selectLoaded = (state: ApplicationState) => nflFeature.selectIsLoaded(state);
  loadGames = NFLCommands.loadGames;
}

import { Component } from '@angular/core';
import { ApplicationState } from '../../state';
import { nhlFeature } from './state';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { NHLCommands } from './state/actions';

@Component({
  selector: 'app-nhl',
  standalone: true,
  imports: [SportWrapperComponent],
  template: `
    <app-sport-wrapper
      sportName="NHL"
      [gamesSelector]="selectNhlGames"
      [errorSelector]="selectError"
      [loadedSelector]="selectLoaded"
      [loadGamesAction]="loadGames"
    ></app-sport-wrapper>
  `,
  styles: ``,
})
export class NhlComponent {
  selectNhlGames = (state: ApplicationState) =>
    nhlFeature.selectNhlGames(state);
  selectError = (state: ApplicationState) => nhlFeature.selectError(state);
  selectLoaded = (state: ApplicationState) => nhlFeature.selectIsLoaded(state);
  loadGames = NHLCommands.loadGames;
}

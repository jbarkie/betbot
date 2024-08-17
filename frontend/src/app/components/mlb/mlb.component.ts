import { Component } from '@angular/core';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { mlbFeature } from './state';
import { MLBCommands } from './state/actions';
import { ApplicationState } from '../../state';

@Component({
  selector: 'app-mlb',
  standalone: true,
  imports: [SportWrapperComponent],
  template: `
    <app-sport-wrapper
      sportName="MLB"
      [gamesSelector]="selectMlbGames"
      [errorSelector]="selectError"
      [loadedSelector]="selectLoaded"
      [loadGamesAction]="loadGames"
    ></app-sport-wrapper>
  `,
  styles: ``
})
export class MlbComponent {
  selectMlbGames = (state: ApplicationState) => mlbFeature.selectMlbGames(state);
  selectError = (state: ApplicationState) => mlbFeature.selectError(state);
  selectLoaded = (state: ApplicationState) => mlbFeature.selectIsLoaded(state);
  loadGames = MLBCommands.loadGames;
}

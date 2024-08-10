import { Component } from '@angular/core';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { mlbFeature, MlbState } from './state';
import { MLBCommands } from './state/actions';

@Component({
  selector: 'app-mlb',
  standalone: true,
  imports: [SportWrapperComponent],
  template: `
    <app-sport-wrapper
      sportName="MLB"
      [gamesSelector]="selectMlbGames"
      [errorSelector]="selectError"
      [loadGamesAction]="loadGames"
    ></app-sport-wrapper>
  `,
  styles: ``
})
export class MlbComponent {
  selectMlbGames = (state: { mlb: MlbState }) => mlbFeature.selectMlbGames(state);
  selectError = (state: { mlb: MlbState }) => mlbFeature.selectError(state);
  loadGames = MLBCommands.loadGames;
}

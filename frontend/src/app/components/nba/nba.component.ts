import { Component, inject } from '@angular/core';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { NBAStore } from '../../services/sports/sports.store';

@Component({
    selector: 'app-nba',
    standalone: true,
    template: `
    <app-sport-wrapper
      sportName="NBA"
      [games]="store.games"
      [error]="store.error"
      [isLoading]="store.isLoading"
      [dateChange]="handleDateChange"
    ></app-sport-wrapper>
  `,
    styles: [],
    imports: [SportWrapperComponent]
})
export class NbaComponent {
  protected readonly store = inject(NBAStore);

  public readonly handleDateChange = (date: Date): void => {
    this.store.loadGames(date);
  }
}

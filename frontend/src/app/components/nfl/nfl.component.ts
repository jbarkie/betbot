import { Component, inject } from '@angular/core';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { NFLStore } from '../../services/sports/sports.store';

@Component({
    selector: 'app-nfl',
    standalone: true,
    imports: [SportWrapperComponent],
    template: `
    <app-sport-wrapper
      sportName="NFL"
      [games]="store.games"
      [error]="store.error"
      [isLoading]="store.isLoading"
      [dateChange]="handleDateChange"
    ></app-sport-wrapper>
  `,
    styles: ``
})
export class NflComponent {
  protected readonly store = inject(NFLStore);

  public readonly handleDateChange = (date: Date): void => {
    this.store.loadGames(date);
  }
}

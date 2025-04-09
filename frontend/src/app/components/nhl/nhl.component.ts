import { Component, inject } from '@angular/core';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { NHLStore } from '../../services/sports/sports.store';

@Component({
  selector: 'app-nhl',
  standalone: true,
  imports: [SportWrapperComponent],
  template: `
    <app-sport-wrapper
      sportName="NHL"
      [games]="store.games()"
      [error]="store.error()"
      [isLoading]="store.isLoading()"
      [dateChange]="handleDateChange"
    ></app-sport-wrapper>
  `,
  styles: ``,
})
export class NhlComponent {
  protected readonly store = inject(NHLStore);

  public readonly handleDateChange = (date: Date): void => {
    this.store.loadGames(date);
  };
}

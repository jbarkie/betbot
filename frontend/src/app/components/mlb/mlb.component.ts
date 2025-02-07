import { Component, inject } from '@angular/core';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { MLBStore } from '../../services/sports/sports.store';

@Component({
    selector: 'app-mlb',
    standalone: true,
    imports: [SportWrapperComponent],
    template: `
    <app-sport-wrapper
      sportName="MLB"
      [games]="store.games()"
      [error]="store.error()"
      [isLoading]="store.isLoading"
      [dateChange]="handleDateChange"
    ></app-sport-wrapper>
  `,
    styles: ``
})
export class MlbComponent {
  protected readonly store = inject(MLBStore);

  public readonly handleDateChange = (date: Date): void => {
    this.store.loadGames(date);
  }
}

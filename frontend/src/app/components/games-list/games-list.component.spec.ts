import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Component, Input } from '@angular/core';

import { GamesListComponent } from './games-list.component';
import { Game } from '../models';

@Component({
  selector: 'app-game',
  template: '<div>Mock Game Component</div>',
})
class MockGameComponent {
  @Input() game!: Game;
}

describe('GamesListComponent', () => {
  let component: GamesListComponent;
  let fixture: ComponentFixture<GamesListComponent>;

  const mockGames: Game[] = [
    {
      id: '1',
      sport: 'NBA',
      homeTeam: 'Boston Celtics',
      awayTeam: 'Los Angeles Lakers',
      date: new Date().toISOString(),
      time: '7:30 PM',
      homeOdds: '-200',
      awayOdds: '+150',
    },
    {
      id: '2',
      sport: 'NBA',
      homeTeam: 'Golden State Warriors',
      awayTeam: 'Miami Heat',
      date: new Date().toISOString(),
      time: '7:30 PM',
      homeOdds: '-150',
      awayOdds: '+120',
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MockGameComponent],
      imports: [GamesListComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(GamesListComponent);
    component = fixture.componentInstance;
    Object.defineProperty(component, 'list', { get: () => () => mockGames });
    Object.defineProperty(component, 'loaded', { get: () => () => true });
    Object.defineProperty(component, 'error', { get: () => () => '' });
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display games when loaded and games are available', () => {
    const gameComponents = fixture.nativeElement.querySelectorAll('app-game');
    expect(gameComponents.length).toBe(2);
  });

  it('should display "No games found for today." when no games are available', () => {
    Object.defineProperty(component, 'list', { get: () => () => [] });
    fixture.detectChanges();

    const alertMessage =
      fixture.nativeElement.querySelector('app-alert-message');
    expect(alertMessage.textContent).toContain('No games found for today.');
  });

  it('should display loading spinner when games are not loaded', () => {
    Object.defineProperty(component, 'loaded', { get: () => () => false });
    fixture.detectChanges();

    const loadingSpinner = fixture.nativeElement.querySelector('.loading');
    expect(loadingSpinner).toBeTruthy();
  });

  it('should display error message when games failed to load', () => {
    Object.defineProperty(component, 'error', { get: () => () => 'Error loading games.' });
    fixture.detectChanges();

    const alertMessage =
      fixture.nativeElement.querySelector('app-alert-message');
    expect(alertMessage.textContent).toContain('Error loading games.');
  });

  it('should track games by id', () => {
    const trackById = component.trackById(0, mockGames[0]);
    expect(trackById).toBe('1');
  });

  it('should not display games when not loaded', () => {
    Object.defineProperty(component, 'loaded', { get: () => () => false });
    fixture.detectChanges();

    const gameComponents = fixture.nativeElement.querySelectorAll('app-game');
    expect(gameComponents.length).toBe(0);
  });

  it('should not display loading spinner when games are loaded', () => {
    const loadingSpinner = fixture.nativeElement.querySelector('.loading');
    expect(loadingSpinner).toBeFalsy();
  });

  it('should not display error message when games are loaded', () => {  
    const alertMessage =
      fixture.nativeElement.querySelector('app-alert-message');
    expect(alertMessage).toBeFalsy();
  });

  it('should not display loading spinner when there is an error', () => {
    Object.defineProperty(component, 'error', { get: () => () => 'Error loading games.' });
    fixture.detectChanges();

    const loadingSpinner = fixture.nativeElement.querySelector('.loading');
    expect(loadingSpinner).toBeFalsy();
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';

import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { AnalyticsService } from '../../services/analytics/analytics.service';
import { Game } from '../models';
import { GameComponent } from './game.component';

describe('GameComponent', () => {
  let component: GameComponent;
  let fixture: ComponentFixture<GameComponent>;

  const mockGame: Game = {
    id: '1',
    sport: 'MLB',
    awayTeam: 'New York Yankees',
    homeTeam: 'Boston Red Sox',
    date: new Date().toISOString(),
    time: '7:00 PM',
    awayOdds: '+110',
    homeOdds: '+110',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GameComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(GameComponent);
    component = fixture.componentInstance;
    Object.defineProperty(component, 'game', { get: () => () => mockGame });
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display team names correctly', () => {
    const teamNames = fixture.nativeElement.querySelectorAll('.card-title');
    expect(teamNames[0].textContent).toContain('New York Yankees');
    expect(teamNames[0].textContent).toContain('Boston Red Sox');
  });

  it('should display game time correctly', () => {
    const timeElement = fixture.nativeElement.querySelector('p');
    expect(timeElement.textContent).toContain('7:00 PM');
  });

  it('should display odds correctly', () => {
    const odds = fixture.nativeElement.querySelectorAll('p');
    expect(odds[1].textContent).toContain('New York Yankees ML: +110');
    expect(odds[2].textContent).toContain('Boston Red Sox ML: +110');
  });

  it('should display "No odds available" when odds are empty', () => {
    const gameWithoutOdds = { ...mockGame, homeOdds: '', awayOdds: '' };
    Object.defineProperty(component, 'game', {
      get: () => () => gameWithoutOdds,
    });

    fixture.detectChanges();

    const odds = fixture.nativeElement.querySelectorAll('p');
    expect(odds[1].textContent).toContain('No odds available');
  });

  it('should generate correct image source for MLB teams', () => {
    const imgElements = fixture.debugElement.queryAll(By.css('img'));
    expect(imgElements[0].attributes['src']).toBe(
      'assets/img/mlb/new-york-yankees.svg'
    );
    expect(imgElements[1].attributes['src']).toBe(
      'assets/img/mlb/boston-red-sox.svg'
    );
  });

  it('should generate correct image source for non-MLB teams', () => {
    const nbaGame: Game = {
      ...mockGame,
      sport: 'NBA',
      awayTeam: 'Los Angeles Lakers',
      homeTeam: 'Boston Celtics',
    };
    Object.defineProperty(component, 'game', { get: () => () => nbaGame });

    fixture.detectChanges();

    const imgElements = fixture.debugElement.queryAll(By.css('img'));
    expect(imgElements[0].attributes['src']).toBe(
      'assets/img/nba/los-angeles-lakers.png'
    );
    expect(imgElements[1].attributes['src']).toBe(
      'assets/img/nba/boston-celtics.png'
    );
  });

  it('should have correct alt text for team logos', () => {
    const imgElements = fixture.debugElement.queryAll(By.css('img'));
    expect(imgElements[0].attributes['alt']).toBe('New York Yankees logo');
    expect(imgElements[1].attributes['alt']).toBe('Boston Red Sox logo');
  });

  describe('analyze', () => {
    it('should have an "Analyze" button', () => {
      const button = fixture.debugElement.query(By.css('button'));
      expect(button.nativeElement.textContent).toBe('Analyze');
    });

    it('should call analyze method on button click', () => {
      jest.spyOn(component, 'analyze');
      const button = fixture.debugElement.query(By.css('button'));
      button.nativeElement.click();
      expect(component.analyze).toHaveBeenCalled();
    });

    it('should call analyticsService.analyze with correct parameters', async () => {
      const analyticsService = TestBed.inject(AnalyticsService);
      jest
        .spyOn(analyticsService, 'analyze')
        .mockReturnValue(of({ gameId: '1' }));

      await component.analyze();

      expect(analyticsService.analyze).toHaveBeenCalled();
    });

    it('should handle errors from analyticsService', async () => {
      const analyticsService = TestBed.inject(AnalyticsService);
      const mockError = new Error('Analysis failed');
      jest
        .spyOn(analyticsService, 'analyze')
        .mockReturnValue(throwError(() => mockError));
      jest.spyOn(console, 'error');

      await component.analyze();

      expect(console.error).toHaveBeenCalledWith(
        'Error analyzing game:',
        mockError
      );
    });
  });

  describe('getImageSrc', () => {
    it('should handle team names with spaces', () => {
      expect(component.getImageSrc('MLB', 'Boston Red Sox')).toBe(
        'assets/img/mlb/boston-red-sox.svg'
      );
    });

    it('should handle team names with periods', () => {
      expect(component.getImageSrc('MLB', 'St. Louis Cardinals')).toBe(
        'assets/img/mlb/st-louis-cardinals.svg'
      );
    });

    it('should return SVG for MLB and PNG for other sports', () => {
      expect(component.getImageSrc('MLB', 'Boston Red Sox')).toContain('.svg');
      expect(component.getImageSrc('NBA', 'Boston Celtics')).toContain('.png');
    });
  });
});

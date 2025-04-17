import { signal, Signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { AuthStore } from '../../services/auth/auth.store';
import { NHLStore } from '../../services/sports/sports.store';
import { Game } from '../models';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { NhlComponent } from './nhl.component';

interface MockNHLStore {
  games: Signal<Game[]>;
  error: Signal<string | null>;
  isLoading: Signal<boolean>;
  loadGames: jest.Mock;
}

const mockAuthStore = {
  isAuthenticated: signal(true),
  showLoginModal: signal(false),
};

describe('NhlComponent', () => {
  let component: NhlComponent;
  let fixture: ComponentFixture<NhlComponent>;
  let mockStore: MockNHLStore;
  const mockDate = new Date('2024-01-01T12:00:00Z');

  beforeEach(async () => {
    const mockGames = [
      {
        id: '1',
        sport: 'NHL',
        homeTeam: 'Boston Bruins',
        awayTeam: 'Montreal Canadiens',
        date: mockDate.toISOString(),
        time: '7:00 PM',
        homeOdds: '-200',
        awayOdds: '+150',
      },
    ];

    mockStore = {
      games: signal(mockGames),
      error: signal(''),
      isLoading: signal(false),
      loadGames: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [NhlComponent, SportWrapperComponent],
      providers: [
        { provide: NHLStore, useValue: mockStore },
        { provide: AuthStore, useValue: mockAuthStore },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NhlComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should use SportWrapperComponent with correct inputs', () => {
    const sportWrapper = fixture.debugElement.query(
      By.directive(SportWrapperComponent)
    );
    expect(sportWrapper).toBeTruthy();
    expect(sportWrapper.componentInstance.sportName()).toBe('NHL');
  });

  it('should handle date changes', () => {
    component.handleDateChange(mockDate);
    expect(mockStore.loadGames).toHaveBeenCalledWith(mockDate);
  });

  it('should provide games to SportWrapperComponent', () => {
    const testGames = [
      {
        id: '1',
        sport: 'NHL',
        homeTeam: 'Boston Bruins',
        awayTeam: 'Montreal Canadiens',
        date: mockDate.toISOString(),
        time: '7:00 PM',
        homeOdds: '-200',
        awayOdds: '+150',
      } as Game,
    ];
    (mockStore.games as any).set(testGames);
    fixture.detectChanges();

    const sportWrapper = fixture.debugElement.query(
      By.directive(SportWrapperComponent)
    );
    expect(sportWrapper.componentInstance.games()).toEqual(testGames);
  });

  it('should handle error states', () => {
    const testError = 'An error occurred';
    (mockStore.error as any).set(testError);
    fixture.detectChanges();

    const sportWrapper = fixture.debugElement.query(
      By.directive(SportWrapperComponent)
    );
    expect(sportWrapper.componentInstance.error()).toBe(testError);
  });

  it('should handle loading states', () => {
    (mockStore.isLoading as any).set(true);
    fixture.detectChanges();

    const sportWrapper = fixture.debugElement.query(
      By.directive(SportWrapperComponent)
    );
    expect(sportWrapper.componentInstance.isLoading()).toBe(true);
  });

  it('should update games when store changes', () => {
    const newGames = [
      {
        id: '2',
        sport: 'NHL',
        homeTeam: 'New York Rangers',
        awayTeam: 'Philadelphia Flyers',
        date: mockDate.toISOString(),
        time: '7:00 PM',
        homeOdds: '-150',
        awayOdds: '+120',
      } as Game,
    ];
    (mockStore.games as any).set(newGames);
    fixture.detectChanges();

    const sportWrapper = fixture.debugElement.query(
      By.directive(SportWrapperComponent)
    );
    expect(sportWrapper.componentInstance.games()).toEqual(newGames);
  });

  it('should integrate with SportWrapperComponent date handling', () => {
    const sportWrapper = fixture.debugElement.query(
      By.directive(SportWrapperComponent)
    );
    const testDate = new Date('2024-02-01');

    sportWrapper.componentInstance.dateChange = () =>
      component.handleDateChange(testDate);
    sportWrapper.componentInstance.loadGames();
    expect(mockStore.loadGames).toHaveBeenCalledWith(testDate);
  });
});

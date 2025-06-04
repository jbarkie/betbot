import { signal, Signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { AuthStore } from '../../services/auth/auth.store';
import { NFLStore } from '../../services/sports/sports.store';
import { Game } from '../models';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { NflComponent } from './nfl.component';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

interface MockNFLStore {
  games: Signal<Game[]>;
  error: Signal<string | null>;
  isLoading: Signal<boolean>;
  loadGames: jest.Mock;
}

const mockAuthStore = {
  isAuthenticated: signal(true),
  showLoginModal: signal(false),
};

describe('NflComponent', () => {
  let component: NflComponent;
  let fixture: ComponentFixture<NflComponent>;
  let mockStore: MockNFLStore;
  const mockDate = new Date('2024-01-01T12:00:00Z');

  beforeEach(async () => {
    const mockGames = [
      {
        id: '1',
        sport: 'NFL',
        homeTeam: 'New England Patriots',
        awayTeam: 'Dallas Cowboys',
        date: mockDate.toISOString(),
        time: '1:00 PM',
        homeOdds: '-150',
        awayOdds: '+200',
      } as Game,
    ];

    mockStore = {
      games: signal(mockGames),
      error: signal(''),
      isLoading: signal(false),
      loadGames: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [NflComponent, SportWrapperComponent],
      providers: [
        { provide: NFLStore, useValue: mockStore },
        { provide: AuthStore, useValue: mockAuthStore },
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NflComponent);
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
    expect(sportWrapper.componentInstance.sportName()).toBe('NFL');
  });

  it('should handle date changes', () => {
    component.handleDateChange(mockDate);
    expect(mockStore.loadGames).toHaveBeenCalledWith(mockDate);
  });

  it('should provide games to sport wrapper', () => {
    const testGames = [
      {
        id: '1',
        sport: 'NFL',
        homeTeam: 'New England Patriots',
        awayTeam: 'Dallas Cowboys',
        date: mockDate.toISOString(),
        time: '1:00 PM',
        homeOdds: '-150',
        awayOdds: '+200',
      } as Game,
    ];

    (mockStore.games as any).set(testGames);
    fixture.detectChanges();

    const sportWrapper = fixture.debugElement.query(
      By.directive(SportWrapperComponent)
    );
    expect(sportWrapper.componentInstance.games()).toEqual(testGames);
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
        sport: 'NFL',
        homeTeam: 'New York Giants',
        awayTeam: 'Philadelphia Eagles',
        date: mockDate.toISOString(),
        time: '4:00 PM',
        homeOdds: '-110',
        awayOdds: '-110',
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

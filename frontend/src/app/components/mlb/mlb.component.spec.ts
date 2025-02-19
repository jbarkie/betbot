import { signal, Signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { Game } from '../../components/models';
import { AuthStore } from '../../services/auth/auth.store';
import { MLBStore } from '../../services/sports/sports.store';
import { SportWrapperComponent } from '../sport-wrapper/sport-wrapper.component';
import { MlbComponent } from './mlb.component';

interface MockMLBStore {
  games: Signal<Game[]>;
  error: Signal<string | null>;
  isLoading: Signal<boolean>;
  loadGames: jest.Mock;
}

const mockAuthStore = {
  isAuthenticated: signal(true),
  showLoginModal: signal(false),
}

describe('MlbComponent', () => {
  let component: MlbComponent;
  let fixture: ComponentFixture<MlbComponent>;
  let mockStore: MockMLBStore;
  const mockDate = new Date('2024-01-01T12:00:00Z');

  beforeEach(async () => {
    const mockGames = [
      {
        id: '1',
        sport: 'MLB',
        homeTeam: 'Boston Red Sox',
        awayTeam: 'New York Yankees',
        date: mockDate.toISOString(),
        time: '7:00 PM',
        homeOdds: '+110',
        awayOdds: '+110',
      } as Game,
    ];

    mockStore = {
      games: signal(mockGames),
      error: signal(''),
      isLoading: signal(false),
      loadGames: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [MlbComponent, SportWrapperComponent],
      providers: [
        { provide: MLBStore, useValue: mockStore },
        { provide: AuthStore, useValue: mockAuthStore },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MlbComponent);
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
    expect(sportWrapper.componentInstance.sportName()).toBe('MLB');
  });

  it('should handle date changes', () => {
    component.handleDateChange(mockDate);
    expect(mockStore.loadGames).toHaveBeenCalledWith(mockDate);
  });

  it('should provide games to sport wrapper', () => {
    const testGames = [
      {
        id: '1',
        sport: 'MLB',
        homeTeam: 'Boston Red Sox',
        awayTeam: 'New York Yankees',
        date: mockDate.toISOString(),
        time: '7:00 PM',
        homeOdds: '+110',
        awayOdds: '+110',
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
    const testError = 'Test error message';
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
    const isLoading = sportWrapper.componentInstance.isLoading();
    expect(isLoading()).toBe(true);
  });

  it('should update games when store changes', () => {
    const newGames = [
      {
        id: '2',
        sport: 'MLB',
        homeTeam: 'Chicago Cubs',
        awayTeam: 'St. Louis Cardinals',
        date: mockDate.toISOString(),
        time: '8:00 PM',
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

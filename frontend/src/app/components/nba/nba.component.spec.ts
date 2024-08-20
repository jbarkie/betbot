import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';

import { NbaComponent } from './nba.component';
import { NBACommands } from './state/actions';

describe('NbaComponent', () => {
  let component: NbaComponent;
  let fixture: ComponentFixture<NbaComponent>;
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NbaComponent],
      providers: [
        provideMockStore({
          initialState: {
            nba: {
              entities: {},
              ids: [],
              isLoaded: false,
              error: '',
            },
          },
        }),
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    fixture = TestBed.createComponent(NbaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should use SportWrapperComponent with correct inputs', () => {
    const sportWrapper =
      fixture.nativeElement.querySelector('app-sport-wrapper');
    expect(sportWrapper).toBeTruthy();
    expect(sportWrapper.getAttribute('sportName')).toBe('NBA');
  });

  it('should select NBA games correctly', () => {
    const mockDate = new Date().toISOString();
    const mockState = {
      nba: {
        entities: {
          '1': {
            id: '1',
            sport: 'NBA',
            homeTeam: 'Boston Celtics',
            awayTeam: 'Los Angeles Lakers',
            date: mockDate,
            time: '7:30 PM',
            homeOdds: '-200',
            awayOdds: '+150',
          },
          '2': {
            id: '2',
            sport: 'NBA',
            homeTeam: 'Golden State Warriors',
            awayTeam: 'Miami Heat',
            date: mockDate,
            time: '7:30 PM',
            homeOdds: '-150',
            awayOdds: '+120',
          },
        },
        ids: ['1', '2'],
        isLoaded: true,
        error: '',
      },
    };

    const result = component.selectNbaGames(mockState as any);
    expect(result).toEqual([
      {
        id: '1',
        sport: 'NBA',
        homeTeam: 'Boston Celtics',
        awayTeam: 'Los Angeles Lakers',
        date: mockDate,
        time: '7:30 PM',
        homeOdds: '-200',
        awayOdds: '+150',
      },
      {
        id: '2',
        sport: 'NBA',
        homeTeam: 'Golden State Warriors',
        awayTeam: 'Miami Heat',
        date: mockDate,
        time: '7:30 PM',
        homeOdds: '-150',
        awayOdds: '+120',
      },
    ]);
  });

  it('should select error correctly', () => {
    const mockState = {
      nba: {
        error: 'An error occurred',
      },
    };
    const result = component.selectError(mockState as any);
    expect(result).toBe('An error occurred');
  });

  it('should select loaded correctly', () => {
    const mockState = {
      nba: {
        isLoaded: true,
      },
    };
    const result = component.selectLoaded(mockState as any);
    expect(result).toBe(true);
  });

  it('should use correct loadGames action', () => {
    expect(component.loadGames).toBe(NBACommands.loadGames);
  });
});

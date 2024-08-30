import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';

import { NflComponent } from './nfl.component';
import { NFLCommands } from './state/actions';

describe('NflComponent', () => {
  let component: NflComponent;
  let fixture: ComponentFixture<NflComponent>;
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NflComponent],
      providers: [
        provideMockStore({
          initialState: {
            nfl: {
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
    fixture = TestBed.createComponent(NflComponent);
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
    expect(sportWrapper.getAttribute('sportName')).toBe('NFL');
  });

  it('should select NFL games correctly', () => {
    const mockDate = new Date().toISOString();
    const mockState = {
      nfl: {
        entities: {
          '1': {
            id: '1',
            sport: 'NFL',
            homeTeam: 'New England Patriots',
            awayTeam: 'Dallas Cowboys',
            date: mockDate,
            time: '1:00 PM',
            homeOdds: '-150',
            awayOdds: '+200',
          },
        },
        ids: ['1'],
        isLoaded: true,
        error: '',
      },
    };

    const result = component.selectNflGames(mockState as any);
    expect(result).toEqual([
      {
        id: '1',
        sport: 'NFL',
        homeTeam: 'New England Patriots',
        awayTeam: 'Dallas Cowboys',
        date: mockDate,
        time: '1:00 PM',
        homeOdds: '-150',
        awayOdds: '+200',
      },
    ]);
  });

  it('should select error correctly', () => {
    const mockState = {
      nfl: {
        error: 'Error loading NFL games',
      },
    };
    const result = component.selectError(mockState as any);
    expect(result).toBe('Error loading NFL games');
  });

  it('should select loaded correctly', () => {
    const mockState = {
      nfl: {
        isLoaded: true,
      },
    };
    const result = component.selectLoaded(mockState as any);
    expect(result).toBe(true);
  });

  it('should use correct loadGames action', () => {
    expect(component.loadGames).toBe(NFLCommands.loadGames);
  });
});

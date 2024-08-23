import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';

import { NhlComponent } from './nhl.component';
import { NHLCommands } from './state/actions';

describe('NhlComponent', () => {
  let component: NhlComponent;
  let fixture: ComponentFixture<NhlComponent>;
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NhlComponent],
      providers: [
        provideMockStore({
          initialState: {
            nhl: {
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
    fixture = TestBed.createComponent(NhlComponent);
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
    expect(sportWrapper.getAttribute('sportName')).toBe('NHL');
  });

  it('should select NHL games correctly', () => {
    const mockDate = new Date().toISOString();
    const mockState = {
      nhl: {
        entities: {
          '1': {
            id: '1',
            sport: 'NHL',
            homeTeam: 'Boston Bruins',
            awayTeam: 'Montreal Canadiens',
            date: mockDate,
            time: '7:30 PM',
            homeOdds: '-200',
            awayOdds: '+150',
          },
        },
        ids: ['1'],
        isLoaded: true,
        error: '',
      },
    };

    const result = component.selectNhlGames(mockState as any);
    expect(result).toEqual([
      {
        id: '1',
        sport: 'NHL',
        homeTeam: 'Boston Bruins',
        awayTeam: 'Montreal Canadiens',
        date: mockDate,
        time: '7:30 PM',
        homeOdds: '-200',
        awayOdds: '+150',
      },
    ]);
  });

  it('should select error correctly', () => {
    const mockState = {
      nhl: {
        entities: {},
        ids: [],
        isLoaded: true,
        error: 'Error loading NHL games',
      },
    };

    const result = component.selectError(mockState as any);
    expect(result).toBe('Error loading NHL games');
  });

  it('should select loaded correctly', () => {
    const mockState = {
      nhl: {
        isLoaded: true,
      },
    };
    const result = component.selectLoaded(mockState as any);
    expect(result).toBe(true);
  });

  it('should use correct loadGames action', () => {
    expect(component.loadGames).toBe(NHLCommands.loadGames);
  });
});

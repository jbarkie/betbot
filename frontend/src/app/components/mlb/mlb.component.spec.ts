import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore, MockStore } from '@ngrx/store/testing';

import { MlbComponent } from './mlb.component';
import { MLBCommands } from './state/actions';

describe('MlbComponent', () => {
  let component: MlbComponent;
  let fixture: ComponentFixture<MlbComponent>;
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MlbComponent],
      providers: [
        provideMockStore({
          initialState: {
            mlb: {
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
    fixture = TestBed.createComponent(MlbComponent);
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
    expect(sportWrapper.getAttribute('sportName')).toBe('MLB');
  });

  it('should select MLB games correctly', () => {
    const mockDate = new Date().toISOString();
    const mockState = {
      mlb: {
        entities: {
          '1': {
            id: '1',
            sport: 'MLB',
            homeTeam: 'Boston Red Sox',
            awayTeam: 'New York Yankees',
            date: mockDate,
            time: '7:00 PM',
            homeOdds: '+110',
            awayOdds: '+110',
          },
        },
        ids: ['1'],
      },
    };
    const result = component.selectMlbGames(mockState as any);
    expect(result).toEqual([
      {
        id: '1',
        sport: 'MLB',
        homeTeam: 'Boston Red Sox',
        awayTeam: 'New York Yankees',
        date: mockDate,
        time: '7:00 PM',
        homeOdds: '+110',
        awayOdds: '+110',
      },
    ]);
  });

  it('should select error correctly', () => {
    const mockState = {
      mlb: {
        error: 'An error occurred',
      },
    };
    const result = component.selectError(mockState as any);
    expect(result).toBe('An error occurred');
  });

  it('should select loaded correctly', () => {
    const mockState = {
      mlb: {
        isLoaded: true,
      },
    };
    const result = component.selectLoaded(mockState as any);
    expect(result).toBe(true);
  });

  it('should use correct loadGames action', () => {
    expect(component.loadGames).toBe(MLBCommands.loadGames);
  });
});

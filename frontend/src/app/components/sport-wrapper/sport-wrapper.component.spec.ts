import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { createSelector } from '@ngrx/store';

import { SportWrapperComponent } from './sport-wrapper.component';
import { Game } from '../models';
import { ApplicationState } from '../../state';

describe('SportWrapperComponent', () => {
  let component: SportWrapperComponent;
  let fixture: ComponentFixture<SportWrapperComponent>;
  let store: MockStore;
  let mockGames: Game[] = [];

  const mockGamesSelector = createSelector(
    (state: ApplicationState) => state,
    () => mockGames
  );

  const mockErrorSelector = createSelector(
    (state: ApplicationState) => state,
    () => ''
  );

  const mockLoadedSelector = createSelector(
    (state: ApplicationState) => state,
    () => true
  );

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SportWrapperComponent],
      providers: [
        provideMockStore({
          selectors: [
            {
              selector: createSelector(
                (state: ApplicationState) => state.auth.isAuthenticated,
                (auth) => auth
              ),
              value: true,
            },
          ],
        }),
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    jest.spyOn(store, 'dispatch');

    fixture = TestBed.createComponent(SportWrapperComponent);
    component = fixture.componentInstance;

    component.sportName = 'Baseball';
    component.gamesSelector = mockGamesSelector;
    component.errorSelector = mockErrorSelector;
    component.loadedSelector = mockLoadedSelector;
    component.loadGamesAction = jest
      .fn()
      .mockReturnValue({ type: 'Load Games ' });

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with current date', () => {
    const today = new Date();
    expect(component.selectedDate.getDate()).toBe(today.getDate());
  });

  it('should load games on init', () => {
    expect(store.dispatch).toHaveBeenCalledWith(component.loadGamesAction({ date: component.selectedDate }));
  });

  it('should navigate to previous day', () => {
    const initialDate = new Date(component.selectedDate);
    component.previousDay();
    expect(component.selectedDate.getDate()).toBe(initialDate.getDate() - 1);
    expect(store.dispatch).toHaveBeenCalledWith(component.loadGamesAction({ date: component.selectedDate }));
  });

  it('should navigate to next day', () => {
    const initialDate = new Date(component.selectedDate);
    component.nextDay();
    const expectedDate = new Date(initialDate);
    expectedDate.setDate(initialDate.getDate() + 1);
    expect(component.selectedDate.toISOString()).toBe(expectedDate.toISOString());
    expect(store.dispatch).toHaveBeenCalledWith(component.loadGamesAction({ date: component.selectedDate }));
  });

  it('should correctly identify current date', () => {
    const today = new Date();

    expect(component.isCurrentDate()).toBeTruthy();
    
    component.selectedDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    expect(component.isCurrentDate()).toBeFalsy();
  });
  
  it('should handle authentication state changes', () => {
    store.overrideSelector(createSelector((state: ApplicationState) => state.auth.isAuthenticated, (auth) => auth), false);
    store.refreshState();
    fixture.detectChanges();

    component.isAuthenticated$.subscribe((isAuthenticated) => {
      expect(isAuthenticated).toBeFalsy();
    });
  });

  it('should show alert message when not authenticated', () => {
    store.overrideSelector(createSelector((state: ApplicationState) => state.auth.isAuthenticated, (auth) => auth), false);
    store.refreshState();
    fixture.detectChanges();
    const alertMessage = fixture.nativeElement.querySelector('app-alert-message');
    expect(alertMessage).toBeTruthy();
    expect(alertMessage.getAttribute('message')).toBe('You must be logged in to access this page.');
  });
});

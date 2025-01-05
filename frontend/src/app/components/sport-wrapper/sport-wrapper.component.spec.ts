import { Signal, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { Store } from '@ngrx/store';
import { BehaviorSubject } from 'rxjs';
import { Game } from '../models';
import { SportWrapperComponent } from './sport-wrapper.component';

describe('SportWrapperComponent', () => {
  let component: SportWrapperComponent;
  let fixture: ComponentFixture<SportWrapperComponent>;
  let mockStore: Partial<Store>;
  let authStateSubject: BehaviorSubject<boolean>;

  beforeEach(async () => {
    authStateSubject = new BehaviorSubject<boolean>(false);
    mockStore = {
      select: jest.fn().mockReturnValue(authStateSubject.asObservable()),
    };

    await TestBed.configureTestingModule({
      imports: [SportWrapperComponent],
      providers: [{ provide: Store, useValue: mockStore }],
    }).compileComponents();

    fixture = TestBed.createComponent(SportWrapperComponent);
    component = fixture.componentInstance;
    
    component.games = signal([]) as Signal<Game[]>;
    component.error = signal(null) as Signal<string | null>;
    component.isLoading = signal(false) as Signal<boolean>;
    component.dateChange = jest.fn();

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with current date', () => {
    const today = new Date();
    expect(component.selectedDate.getDate()).toBe(today.getDate());
  });

  it('should emit date change on previous day', () => {
    const initialDate = component.selectedDate;
    component.previousDay();

    expect(component.dateChange).toHaveBeenCalledWith(
      new Date(initialDate.getTime() - 24 * 60 * 60 * 1000)
    );
  });

  it('should emit date change on next day', () => {
    const initialDate = component.selectedDate;
    component.nextDay();

    expect(component.dateChange).toHaveBeenCalledWith(
      new Date(initialDate.getTime() + 24 * 60 * 60 * 1000)
    );
  });

  it('should detect current date correctly', () => {
    const today = new Date();
    component.selectedDate = today;
    expect(component.isCurrentDate()).toBe(true);

    component.selectedDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    expect(component.isCurrentDate()).toBe(false);
  });

  it('should handle authentication state changes', () => {
    authStateSubject.next(false);
    fixture.detectChanges();

    component.isAuthenticated$.subscribe((isAuthenticated) => {
      expect(isAuthenticated).toBeFalsy();
    });
  });

  it('should show alert message when not authenticated', async () => {
    authStateSubject.next(false);
    fixture.detectChanges();
    await fixture.whenStable();

    const alertMessage = fixture.debugElement.query(
      By.css('app-alert-message')
    );
    expect(alertMessage).toBeTruthy();
    expect(alertMessage.attributes['message']).toBe(
      'You must be logged in to access this page.'
    );

    // Verify date navigation is not shown
    const buttons = fixture.debugElement.queryAll(By.css('.btn'));
    expect(buttons.length).toBe(0);
  });

  it('should render date navigation correctly when authenticated', async () => {
    // Set authenticated state and provide some games
    authStateSubject.next(true);
    (component.games as any) = signal([{ id: '1', sport: 'TEST', homeTeam: 'Home team', awayTeam: 'Away team' } as Game]); // Create new signal with games
    fixture.detectChanges();
    await fixture.whenStable();
    
    // Verify authentication alert is not shown
    const authAlert = fixture.debugElement.query(
      By.css('app-alert-message[message="You must be logged in to access this page."]')
    );
    expect(authAlert).toBeFalsy();
    
    // Verify navigation buttons
    const buttons = fixture.debugElement.queryAll(By.css('.btn'));
    expect(buttons.length).toBeGreaterThanOrEqual(3);
  
    const dateButton = buttons[1];
    const today = new Date();
    expect(dateButton.nativeElement.textContent.trim()).toContain(
      today.toLocaleDateString('en-US', { 
        weekday: 'long', 
        month: 'long', 
        day: 'numeric' 
      })
    );
  });

  it('should disable previous day button on current date when authenticated', async () => {
    // Set authenticated state
    authStateSubject.next(true);
    component.selectedDate = new Date();
    fixture.detectChanges();
    await fixture.whenStable();
  
    const prevButton = fixture.debugElement.queryAll(By.css('.btn'))[0];
    expect(prevButton.nativeElement.disabled).toBe(true);
  });
});
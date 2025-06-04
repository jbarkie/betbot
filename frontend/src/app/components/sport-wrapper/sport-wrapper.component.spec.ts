import { Signal, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { AuthStore } from '../../services/auth/auth.store';
import { Game } from '../models';
import { SportWrapperComponent } from './sport-wrapper.component';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

const mockAuthStore = {
  isAuthenticated: jest.fn(),
}

describe('SportWrapperComponent', () => {
  let component: SportWrapperComponent;
  let fixture: ComponentFixture<SportWrapperComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SportWrapperComponent],
      providers: [
        { provide: AuthStore, useValue: mockAuthStore },
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SportWrapperComponent);
    component = fixture.componentInstance;

    const mockDateChangeHandler = jest.fn();
    
    (component.games as unknown as Signal<Game[]>) = signal([]);
    (component.isLoading as unknown as Signal<boolean>) = signal(false);
    (component.error as unknown as Signal<string | null>) = signal(null);
    (component.sportName as unknown as Signal<string>) = signal('Test Sport');
    (component.dateChange as unknown as Signal<(date: Date) => void>) = signal(mockDateChangeHandler);

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
    const expectedDate = new Date(initialDate.getTime() - 24 * 60 * 60 * 1000);
    
    component.previousDay();
    
    const dateChangeHandler = component.dateChange();
    expect(dateChangeHandler).toHaveBeenCalledWith(expectedDate);
  });

  it('should emit date change on next day', () => {
    const initialDate = component.selectedDate;
    const expectedDate = new Date(initialDate.getTime() + 24 * 60 * 60 * 1000);
    
    component.nextDay();
    
    const dateChangeHandler = component.dateChange();
    expect(dateChangeHandler).toHaveBeenCalledWith(expectedDate);
  });

  it('should detect current date correctly', () => {
    const today = new Date();
    component.selectedDate = today;
    expect(component.isCurrentDate()).toBe(true);

    component.selectedDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    expect(component.isCurrentDate()).toBe(false);
  });

  it('should show alert message when not authenticated', async () => {
    mockAuthStore.isAuthenticated.mockReturnValue(false);
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
    mockAuthStore.isAuthenticated.mockReturnValue(true);
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
    mockAuthStore.isAuthenticated.mockReturnValue(true);
    component.selectedDate = new Date();
    fixture.detectChanges();
    await fixture.whenStable();
  
    const prevButton = fixture.debugElement.queryAll(By.css('.btn'))[0];
    expect(prevButton.nativeElement.disabled).toBe(true);
  });

  it('should handle non-existing dateChange handler gracefully', () => {
    // These should not throw errors
    expect(() => component.previousDay()).not.toThrow();
    expect(() => component.nextDay()).not.toThrow();
  });
});
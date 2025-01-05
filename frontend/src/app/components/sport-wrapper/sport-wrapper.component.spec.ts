import { Signal, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { Store } from '@ngrx/store';
import { of } from 'rxjs';
import { Game } from '../models';
import { SportWrapperComponent } from './sport-wrapper.component';

describe('SportWrapperComponent', () => {
  let component: SportWrapperComponent;
  let fixture: ComponentFixture<SportWrapperComponent>;
  let mockStore: Partial<Store>;
  let mockGames: Game[] = [];

  beforeEach(async () => {
    mockStore = {
      select: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [SportWrapperComponent],
      providers: [{ provide: Store, useValue: mockStore }],
    }).compileComponents();

    fixture = TestBed.createComponent(SportWrapperComponent);
    component = fixture.componentInstance;
    component.games = signal([]);
    component.error = signal(null);
    component.isLoading = signal(false);
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
    (mockStore.select as jest.Mock).mockReturnValue(of(false));
    fixture.detectChanges();

    component.isAuthenticated$.subscribe((isAuthenticated) => {
      expect(isAuthenticated).toBeFalsy();
    });
  });

  it('should show alert message when not authenticated', () => {
    (mockStore.select as jest.Mock).mockReturnValue(of(false));
    fixture.detectChanges();

    const alertMessage = fixture.debugElement.query(
      By.css('app-alert-message')
    );
    expect(alertMessage).toBeTruthy();
    expect(alertMessage.attributes['message']).toBe(
      'You must be logged in to access this page.'
    );
  });

  it('should render date navigation correctly', () => {
    const buttons = fixture.debugElement.queryAll(By.css('.btn'));
    expect(buttons.length).toBe(3); // Previous, Current, Next

    const dateButton = buttons[1];
    const today = new Date();
    const expectedDateText = today.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });

    expect(dateButton.nativeElement.textContent.trim()).toContain(
      expectedDateText
    );
  });

  it('should disable previous day button on current date', () => {
    component.selectedDate = new Date();
    fixture.detectChanges();

    const prevButton = fixture.debugElement.queryAll(By.css('.btn'))[0];
    expect(prevButton.properties['disabled']).toBe(true);
  });
});

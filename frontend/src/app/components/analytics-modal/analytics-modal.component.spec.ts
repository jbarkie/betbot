import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AnalyticsModalComponent } from './analytics-modal.component';
import { AnalyticsResponse } from '../models';

describe('AnalyticsModalComponent', () => {
  let component: AnalyticsModalComponent;
  let fixture: ComponentFixture<AnalyticsModalComponent>;

  const mockAnalytics: AnalyticsResponse = {
    id: '1',
    home_team: 'Boston Red Sox',
    away_team: 'New York Yankees',
    predicted_winner: 'Boston Red Sox',
    win_probability: 0.65,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalyticsModalComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AnalyticsModalComponent);
    component = fixture.componentInstance;
    Object.defineProperty(component, 'analytics', {
      get: () => () => mockAnalytics,
    });
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display the matchup correctly', () => {
    const matchupElement = fixture.nativeElement.querySelector('p');
    expect(matchupElement.textContent).toContain(
      'New York Yankees @ Boston Red Sox'
    );
  });

  it('should display the predicted winner', () => {
    const winnerElement = fixture.nativeElement.querySelector('.text-primary');
    expect(winnerElement.textContent.trim()).toBe('Boston Red Sox');
  });

  it('should display the win probability as a percentage', () => {
    const probabilityElement = fixture.nativeElement.querySelector(
      '.text-base-content\\/70'
    );
    expect(probabilityElement.textContent).toContain('65.0%');
  });

  it('should emit close event when close button is clicked', () => {
    const closeSpy = jest.spyOn(component.close, 'emit');
    const closeButton = fixture.nativeElement.querySelector('.btn');

    closeButton.click();

    expect(closeSpy).toHaveBeenCalled();
  });
});

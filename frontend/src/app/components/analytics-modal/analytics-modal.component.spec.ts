import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AnalyticsModalComponent } from './analytics-modal.component';
import { AnalyticsResponse } from '../models';

const mlAnalytics: AnalyticsResponse = {
  id: '1',
  home_team: 'Boston Red Sox',
  away_team: 'New York Yankees',
  predicted_winner: 'Boston Red Sox',
  win_probability: 0.65,
  home_win_probability: 0.65,
  away_win_probability: 0.35,
  prediction_method: 'machine_learning',
};

const ruleBasedAnalytics: AnalyticsResponse = {
  id: '2',
  home_team: 'Boston Red Sox',
  away_team: 'New York Yankees',
  predicted_winner: 'New York Yankees',
  win_probability: 0.58,
  prediction_method: 'rule_based',
};

function createFixture(analytics: AnalyticsResponse): ComponentFixture<AnalyticsModalComponent> {
  const fixture = TestBed.createComponent(AnalyticsModalComponent);
  const component = fixture.componentInstance;
  Object.defineProperty(component, 'analytics', {
    get: () => () => analytics,
  });
  fixture.detectChanges();
  return fixture;
}

describe('AnalyticsModalComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalyticsModalComponent],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = createFixture(mlAnalytics);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display the matchup correctly', () => {
    const fixture = createFixture(mlAnalytics);
    const matchupElement = fixture.nativeElement.querySelector('p');
    expect(matchupElement.textContent).toContain('New York Yankees @ Boston Red Sox');
  });

  it('should display the predicted winner', () => {
    const fixture = createFixture(mlAnalytics);
    const winnerElement = fixture.nativeElement.querySelector('.text-primary');
    expect(winnerElement.textContent.trim()).toBe('Boston Red Sox');
  });

  it('should emit close event when close button is clicked', () => {
    const fixture = createFixture(mlAnalytics);
    const closeSpy = jest.spyOn(fixture.componentInstance.close, 'emit');
    const closeButton = fixture.nativeElement.querySelector('.btn');
    closeButton.click();
    expect(closeSpy).toHaveBeenCalled();
  });

  describe('win probability display', () => {
    it('should display home and away win percentages from ML response', () => {
      const fixture = createFixture(mlAnalytics);
      const homePct = fixture.nativeElement.querySelector('[data-testid="home-win-pct"]');
      const awayPct = fixture.nativeElement.querySelector('[data-testid="away-win-pct"]');
      expect(homePct.textContent).toContain('65.0%');
      expect(awayPct.textContent).toContain('35.0%');
    });

    it('should derive home and away win percentages from rule-based response', () => {
      const fixture = createFixture(ruleBasedAnalytics);
      const homePct = fixture.nativeElement.querySelector('[data-testid="home-win-pct"]');
      const awayPct = fixture.nativeElement.querySelector('[data-testid="away-win-pct"]');
      // predicted_winner is away team (Yankees), so away gets win_probability (0.58)
      expect(awayPct.textContent).toContain('58.0%');
      expect(homePct.textContent).toContain('42.0%');
    });

    it('should render two probability bar segments', () => {
      const fixture = createFixture(mlAnalytics);
      const segments = fixture.nativeElement.querySelectorAll('.bg-secondary, .bg-primary');
      expect(segments.length).toBe(2);
    });
  });
});

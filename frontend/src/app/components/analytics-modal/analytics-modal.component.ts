import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, input, output } from '@angular/core';

import { AnalyticsResponse } from '../models';

@Component({
  selector: 'app-analytics-modal',
  standalone: true,
  imports: [DatePipe, DecimalPipe],
  template: `
    <div class="modal-box w-11/12 max-w-2xl">
      <h3 class="font-bold text-lg mb-4">Game Analytics</h3>

      <div class="space-y-4">
        <!-- Game Info -->
        <div class="bg-base-200 p-4 rounded-lg">
          <h4 class="font-semibold text-base mb-2">Matchup</h4>
          <p class="text-center text-lg">
            {{ analytics().away_team }} &#64; {{ analytics().home_team }}
          </p>
        </div>

        @if (marketImplied()) {
          <section class="bg-base-200 p-4 rounded-lg" data-testid="nba-team-comparison">
            <h4 class="font-semibold text-base mb-2">Team Form &amp; Matchup</h4>
            @if (analytics().team_comparison; as comparison) {
              <p class="text-sm text-base-content/70 mb-2">
                Completed regular-season games before {{ comparison.before | date:'MMM d, y' }}
                (Eastern). Source: <a class="link" href="https://www.espn.com/nba/scoreboard">ESPN NBA scores</a>.
              </p>
              @if (comparison.away.incomplete || comparison.home.incomplete) {
                <p class="text-sm font-medium mb-2" data-testid="nba-incomplete-results">
                  Records and averages may be incomplete. ESPN reported a tied final score that was excluded.
                </p>
              }
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th scope="col">Metric</th>
                    <th scope="col">{{ analytics().away_team }}</th>
                    <th scope="col">{{ analytics().home_team }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (row of nbaRecordRows; track row.key) {
                    <tr>
                      <th scope="row">{{ row.label }}</th>
                      @for (side of matchupSides; track side) {
                        @let record = comparison[side][row.key];
                        <td>{{ record.wins }}–{{ record.losses }}</td>
                      }
                    </tr>
                  }
                  @for (row of nbaMarginRows; track row.key) {
                    <tr>
                      <th scope="row">{{ row.label }}</th>
                      @for (side of matchupSides; track side) {
                        @let margin = comparison[side][row.key];
                        <td>{{ margin == null ? '—' : (margin >= 0.05 ? '+' : '') + (margin | number:'1.1-1') }}</td>
                      }
                    </tr>
                  }
                  <tr>
                    <th scope="row">Latest result</th>
                    @for (side of matchupSides; track side) {
                      <td>{{ (comparison[side].latest_result | date:'MMM d') ?? '—' }}</td>
                    }
                  </tr>
                </tbody>
              </table>
            } @else {
              <p class="text-sm text-base-content/70">ESPN team results are unavailable for this matchup.</p>
            }
          </section>
        }

        @if (!marketImplied() || analytics().win_probability != null) {
        <!-- Prediction -->
        <div class="bg-base-200 p-4 rounded-lg">
          <h4 class="font-semibold text-base mb-2">
            {{ marketImplied() ? 'Market Favorite' : 'Prediction' }}
          </h4>
          <p class="text-lg font-bold text-primary text-center">
            {{ analytics().predicted_winner ?? 'No favorite' }}
          </p>
        </div>

        <!-- Win Probability Bar -->
        <div class="bg-base-200 p-4 rounded-lg">
          <h4 class="font-semibold text-base mb-3">
            {{ marketImplied() ? 'Market-Implied Win Probability' : 'Win Probability' }}
          </h4>
          <div class="flex justify-between text-sm font-medium mb-1">
            <span data-testid="away-win-pct">
              {{ awayPct() }}%
            </span>
            <span data-testid="home-win-pct">
              {{ homePct() }}%
            </span>
          </div>
          <div class="w-full bg-base-300 rounded-full h-4 flex overflow-hidden">
            <div
              class="bg-secondary h-4 transition-all duration-500"
              [style.width.%]="awayPct()"
            ></div>
            <div
              class="bg-primary h-4 transition-all duration-500"
              [style.width.%]="homePct()"
            ></div>
          </div>
          <div class="flex justify-between text-xs mt-1 text-base-content/70">
            <span>{{ analytics().away_team }}</span>
            <span>{{ analytics().home_team }}</span>
          </div>
        </div>
        } @else {
          <p class="bg-base-200 p-4 rounded-lg text-sm" data-testid="nba-market-unavailable">
            Market probabilities are unavailable: both moneylines are needed.
          </p>
        }

        <!-- Key Factors -->
        @if (analytics().key_factors) {
          <div class="bg-base-200 p-4 rounded-lg">
            <h4 class="font-semibold text-base mb-2">
              {{ marketImplied() ? 'Moneyline Details' : 'Key Factors' }}
            </h4>
            <ul class="space-y-1">
              @for (entry of keyFactorEntries(); track entry[0]) {
                <li class="text-sm text-base-content/70">{{ entry[1] }}</li>
              }
            </ul>
          </div>
        }
      </div>

      <div class="modal-action">
        <button class="btn" (click)="close.emit()">Close</button>
      </div>
    </div>
  `,
  // daisyUI's modal grid needs .modal-box as a direct child next to
  // .modal-backdrop, so the host element must not create its own box.
  styles: [':host { display: contents; }'],
})
export class AnalyticsModalComponent {
  analytics = input.required<AnalyticsResponse>();
  close = output<void>();

  marketImplied = computed(() => this.analytics().prediction_method === 'market_implied');

  protected readonly matchupSides = ['away', 'home'] as const;
  protected readonly nbaRecordRows = [
    { key: 'season_record', label: 'Season record' },
    { key: 'recent_record', label: 'Last 10 record' },
    { key: 'venue_record', label: 'Road / home record' },
    { key: 'head_to_head_record', label: 'Season head-to-head' },
  ] as const;
  protected readonly nbaMarginRows = [
    { key: 'season_margin', label: 'Season point margin / game' },
    { key: 'recent_margin', label: 'Last 10 point margin / game' },
  ] as const;

  homePct = computed(() => {
    const a = this.analytics();
    if (a.home_win_probability != null) {
      return (a.home_win_probability * 100).toFixed(1);
    }
    if (a.win_probability == null) return null;
    const prob = a.predicted_winner === a.home_team ? a.win_probability : 1 - a.win_probability;
    return (prob * 100).toFixed(1);
  });

  awayPct = computed(() => {
    const a = this.analytics();
    if (a.away_win_probability != null) {
      return (a.away_win_probability * 100).toFixed(1);
    }
    if (a.win_probability == null) return null;
    const prob = a.predicted_winner === a.away_team ? a.win_probability : 1 - a.win_probability;
    return (prob * 100).toFixed(1);
  });

  keyFactorEntries = computed(() =>
    Object.entries(this.analytics().key_factors ?? {})
  );
}

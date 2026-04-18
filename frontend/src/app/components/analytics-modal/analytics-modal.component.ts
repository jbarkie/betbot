import { Component, computed, input, output } from '@angular/core';

import { AnalyticsResponse } from '../models';

@Component({
  selector: 'app-analytics-modal',
  standalone: true,
  imports: [],
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

        <!-- Prediction -->
        <div class="bg-base-200 p-4 rounded-lg">
          <h4 class="font-semibold text-base mb-2">Prediction</h4>
          <p class="text-lg font-bold text-primary text-center">
            {{ analytics().predicted_winner }}
          </p>
        </div>

        <!-- Win Probability Bar -->
        <div class="bg-base-200 p-4 rounded-lg">
          <h4 class="font-semibold text-base mb-3">Win Probability</h4>
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

        <!-- Key Factors -->
        @if (analytics().key_factors) {
          <div class="bg-base-200 p-4 rounded-lg">
            <h4 class="font-semibold text-base mb-2">Key Factors</h4>
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
  styles: [],
})
export class AnalyticsModalComponent {
  analytics = input.required<AnalyticsResponse>();
  close = output<void>();

  homePct = computed(() => {
    const a = this.analytics();
    if (a.home_win_probability != null) {
      return (a.home_win_probability * 100).toFixed(1);
    }
    const prob = a.predicted_winner === a.home_team ? a.win_probability : 1 - a.win_probability;
    return (prob * 100).toFixed(1);
  });

  awayPct = computed(() => {
    const a = this.analytics();
    if (a.away_win_probability != null) {
      return (a.away_win_probability * 100).toFixed(1);
    }
    const prob = a.predicted_winner === a.away_team ? a.win_probability : 1 - a.win_probability;
    return (prob * 100).toFixed(1);
  });

  keyFactorEntries = computed(() =>
    Object.entries(this.analytics().key_factors ?? {})
  );
}

import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AnalyticsResponse } from '../models';

@Component({
  selector: 'app-analytics-modal',
  standalone: true,
  imports: [CommonModule],
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
          <div class="text-center">
            <p class="text-lg font-bold text-primary">
              {{ analytics().predicted_winner }}
            </p>
            <p class="text-sm text-base-content/70">
              Win Probability:
              {{ (analytics().win_probability * 100).toFixed(1) }}%
            </p>
          </div>
        </div>

        <!-- Probability Bar -->
        <div class="bg-base-200 p-4 rounded-lg">
          <h4 class="font-semibold text-base mb-2">Win Probability</h4>
          <div class="w-full bg-base-300 rounded-full h-4">
            <div
              class="bg-primary h-4 rounded-full transition-all duration-500"
              [style.width.%]="analytics().win_probability * 100"
            ></div>
          </div>
          <div class="flex justify-between text-xs mt-1">
            <span>{{ analytics().away_team }}</span>
            <span>{{ analytics().home_team }}</span>
          </div>
        </div>

        <!-- Additional Insights Placeholder -->
        <div class="bg-base-200 p-4 rounded-lg">
          <h4 class="font-semibold text-base mb-2">Insights</h4>
          <p class="text-sm text-base-content/70">
            Based on historical performance, team statistics, and current form
            analysis.
          </p>
        </div>
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
}

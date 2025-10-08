import { Component, inject, input, signal } from '@angular/core';
import { AnalyticsRequest, Game, AnalyticsResponse } from '../models';
import { AnalyticsService } from '../../services/analytics/analytics.service';
import { firstValueFrom } from 'rxjs';
import { GameTimePipe } from '../../pipes/game-time.pipe';
import { AnalyticsModalComponent } from '../analytics-modal/analytics-modal.component';

@Component({
  selector: 'app-game',
  standalone: true,
  imports: [GameTimePipe, AnalyticsModalComponent],
  schemas: [],
  template: ` <div
      class="card card-side bg-base-100 shadow-xl mx-auto my-5 max-w-2xl"
    >
      <figure>
        <img
          [src]="getImageSrc(game().sport, game().awayTeam)"
          [alt]="game().awayTeam + ' logo'"
          class="w-28 mx-5"
        />
      </figure>
      <div class="card-body">
        <h2 class="card-title">
          {{ game().awayTeam }} &#64; <br />
          {{ game().homeTeam }}
        </h2>
        <div class="text-sm text-base-content/70">
          <p>{{ game().time | gameTime }}</p>
        </div>
        @if (game().homeOdds === '' && game().awayOdds === '') {
        <p class="text-md">No odds available</p>
        } @else {
        <p>{{ game().awayTeam }} ML: {{ game().awayOdds }}</p>
        <p>{{ game().homeTeam }} ML: {{ game().homeOdds }}</p>
        }
        <div class="card-actions justify-end">
          <button
            (click)="analyze()"
            class="btn btn-primary"
            [disabled]="isAnalyzing()"
          >
            @if (isAnalyzing()) {
            <span class="loading loading-spinner loading-sm"></span>
            } Analyze
          </button>
        </div>
      </div>
      <figure>
        <img
          [src]="getImageSrc(game().sport, game().homeTeam)"
          [alt]="game().homeTeam + ' logo'"
          class="w-28 mx-5"
        />
      </figure>
    </div>

    <!-- Analytics Modal -->
    @if (analyticsData()) {
    <input type="checkbox" id="analytics-modal" class="modal-toggle" checked />
    <div class="modal" role="dialog">
      <div class="modal-backdrop" (click)="closeAnalyticsModal()"></div>
      <app-analytics-modal
        [analytics]="analyticsData()!"
        (close)="closeAnalyticsModal()"
      ></app-analytics-modal>
    </div>
    }`,
  styles: [],
})
export class GameComponent {
  game = input.required<Game>();
  private analyticsService = inject(AnalyticsService);

  isAnalyzing = signal(false);
  analyticsData = signal<AnalyticsResponse | null>(null);

  getImageSrc(sport: string, teamString: string) {
    const teamName = this.normalizeTeamName(teamString);
    const extension = sport === 'MLB' ? 'svg' : 'png';
    return `assets/img/${sport.toLowerCase()}/${teamName}.${extension}`;
  }

  private normalizeTeamName(teamName: string): string {
    return teamName.toLowerCase().replace(/\./g, '').replace(/\s+/g, '-');
  }

  async analyze() {
    if (this.isAnalyzing()) return;

    this.isAnalyzing.set(true);
    try {
      const response = await firstValueFrom(
        this.analyticsService.analyze(
          { gameId: this.game().id } as AnalyticsRequest,
          this.game().sport
        )
      );
      this.analyticsData.set(response);
    } catch (error) {
      console.error('Error analyzing game:', error);
      // You could add a toast notification here for error handling
    } finally {
      this.isAnalyzing.set(false);
    }
  }

  closeAnalyticsModal() {
    this.analyticsData.set(null);
  }
}

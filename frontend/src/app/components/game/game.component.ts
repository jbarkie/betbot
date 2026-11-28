import { Component, ElementRef, effect, inject, input, signal, viewChild } from '@angular/core';
import { Game, AnalyticsResponse } from '../models';
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
            data-testid="analyze-game"
            class="btn btn-primary"
            [disabled]="isAnalyzing()"
          >
            @if (isAnalyzing()) {
            <span class="loading loading-spinner loading-sm"></span>
            } Analyze
          </button>
        </div>
        @if (analyticsError(); as message) {
        <p role="alert" data-testid="analytics-error" class="text-sm text-error">
          {{ message }}
        </p>
        }
      </div>
      <figure>
        <img
          [src]="getImageSrc(game().sport, game().homeTeam)"
          [alt]="game().homeTeam + ' logo'"
          class="w-28 mx-5"
        />
      </figure>
    </div>

    <!-- Analytics Modal: a native modal dialog, so focus is trapped, the
         page behind is inert, and Escape or a backdrop click closes it. -->
    <dialog
      #analyticsDialog
      class="modal"
      aria-label="Game analytics"
      data-testid="analytics-dialog"
      (close)="closeAnalyticsModal()"
    >
      @if (analyticsData(); as analytics) {
      <app-analytics-modal
        [analytics]="analytics"
        (close)="analyticsDialog.close()"
      ></app-analytics-modal>
      }
      <form method="dialog" class="modal-backdrop">
        <button tabindex="-1">Close</button>
      </form>
    </dialog>`,
  styles: [],
})
export class GameComponent {
  game = input.required<Game>();
  private analyticsService = inject(AnalyticsService);

  isAnalyzing = signal(false);
  analyticsData = signal<AnalyticsResponse | null>(null);
  analyticsError = signal<string | null>(null);

  private analyticsDialog = viewChild.required<ElementRef<HTMLDialogElement>>('analyticsDialog');

  constructor() {
    // Open the dialog once analytics arrive; closing it clears them.
    effect(() => {
      const dialog = this.analyticsDialog().nativeElement;
      const hasAnalytics = this.analyticsData() !== null;
      if (hasAnalytics && !dialog.open) {
        dialog.showModal();
      } else if (!hasAnalytics && dialog.open) {
        dialog.close();
      }
    });
  }

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
    this.analyticsError.set(null);
    try {
      const response = await firstValueFrom(
        this.analyticsService.analyze(
          { gameId: this.game().id },
          this.game().sport
        )
      );
      this.analyticsData.set(response);
    } catch {
      this.analyticsError.set('Game analytics are unavailable. Please try again.');
    } finally {
      this.isAnalyzing.set(false);
    }
  }

  closeAnalyticsModal() {
    this.analyticsData.set(null);
  }
}

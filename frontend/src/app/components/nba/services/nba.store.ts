import { computed, inject } from '@angular/core';
import {
  signalStore,
  withState,
  withComputed,
  withMethods,
  patchState,
} from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, switchMap, tap } from 'rxjs';
import { tapResponse } from '@ngrx/operators';
import { HttpClient, HttpParams } from '@angular/common/http';
import { DatePipe } from '@angular/common';
import { Game } from '../../models';
import { environment } from '../../../../environments/environment';

interface NBAState {
  games: Game[];
  isLoading: boolean;
  error: string | null;
}

const initialState: NBAState = {
  games: [],
  isLoading: false,
  error: null,
};

export const NBAStore = signalStore(
  withState(initialState),
  withComputed(({ games }) => ({
    gamesCount: computed(() => games().length),
    hasGames: computed(() => games().length > 0),
  })),
  withMethods((store, httpClient = inject(HttpClient)) => {
    const baseUrl = environment.apiUrl;

    return {
      loadGames: rxMethod<Date>(
        pipe(
          tap(() => {
            patchState(store, { isLoading: true, error: null });
          }),
          switchMap((date) => {
            const datePipe = new DatePipe('en-US');
            const formattedDate = datePipe.transform(date, 'yyyy-MM-dd');
            const params = formattedDate
              ? new HttpParams().set('date', formattedDate)
              : new HttpParams();

            return httpClient
              .get<{ list: Game[] }>(`${baseUrl}/nba/games`, {
                params,
                responseType: 'json',
              })
              .pipe(
                tapResponse({
                  next: (response) => {
                    patchState(store, {
                      games: response.list,
                      isLoading: false,
                    });
                  },
                  error: (error: unknown) => {
                    const errorMessage =
                      (error as Error).message ?? 'An error occurred';
                    patchState(store, {
                      error: errorMessage,
                      games: [],
                    });
                  },
                })
              );
          })
        )
      ),
    };
  })
);

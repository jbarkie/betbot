import { computed, inject } from '@angular/core';
import { signalStore, withState, withComputed, withMethods, patchState } from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, switchMap, tap } from 'rxjs';
import { tapResponse } from '@ngrx/operators';
import { HttpClient, HttpParams } from '@angular/common/http';
import { DatePipe } from '@angular/common';
import { Game } from '../../components/models';
import { environment } from '../../../environments/environment';

export interface SportsState {
  games: Game[];
  isLoading: boolean;
  error: string | null;
}

const initialState: SportsState = {
  games: [],
  isLoading: false,
  error: null,
};

export const createSportsStore = (sport: string) => {
  return signalStore(
    { providedIn: 'root' },
    withState<SportsState>(initialState),
    withComputed(({ games }) => ({
      gamesCount: computed(() => games().length),
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
                .get<{ list: Game[] }>(`${baseUrl}/${sport.toLowerCase()}/games`, {
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
                    error: (error: Error) => {
                      patchState(store, {
                        error: error.message ?? `An error occurred loading ${sport} games`,
                        isLoading: false,
                        games: [],
                      });
                    },
                  })
                );
            })
          )
        ),
        clearError: () => {
          patchState(store, { error: null });
        }
      };
    })
  );
};

export const NBAStore = createSportsStore('NBA');
export const NFLStore = createSportsStore('NFL');
export const MLBStore = createSportsStore('MLB');
export const NHLStore = createSportsStore('NHL');

export type SportsStore = ReturnType<typeof createSportsStore>;
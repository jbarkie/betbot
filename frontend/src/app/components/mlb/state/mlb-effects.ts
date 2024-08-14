import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { environment } from '../../../../environments/environment';
import { MLBCommands, MLBDocuments } from './actions';
import { catchError, map, of, switchMap } from 'rxjs';
import { DatePipe } from '@angular/common';
import { Game } from '../../models';

@Injectable()
export class MlbEffects {
  constructor(private actions$: Actions, private httpClient: HttpClient) {}

  readonly baseUrl = environment.apiUrl;

  loadGames$ = createEffect(() =>
    this.actions$.pipe(
      ofType(MLBCommands.loadGames),
      switchMap((action) => {
        const datePipe = new DatePipe('en-US');
        const formattedDate = datePipe.transform(action.date, 'yyyy-MM-dd');
        const params = formattedDate
          ? new HttpParams().set('date', formattedDate)
          : new HttpParams();
        return this.httpClient
          .get<{ list: Game[] }>(this.baseUrl + '/mlb/games', {
            params,
            responseType: 'json',
          })
          .pipe(
            map((response) => response.list),
            map((payload) => MLBDocuments.games({ payload })),
            catchError((error) => {
              return of(MLBCommands.loadGamesError({ error }));
            })
          );
      })
    )
  );
}

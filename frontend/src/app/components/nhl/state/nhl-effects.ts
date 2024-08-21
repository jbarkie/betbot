import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Actions, ofType } from '@ngrx/effects';
import { environment } from '../../../../environments/environment';
import { createEffect } from '@ngrx/effects';
import { NHLCommands, NHLDocuments } from './actions';
import { DatePipe } from '@angular/common';
import { Game } from '../../models';
import { catchError, map, of, switchMap } from 'rxjs';

@Injectable()
export class NhlEffects {
  constructor(private actions$: Actions, private httpClient: HttpClient) {}

  readonly baseUrl = environment.apiUrl;

  loadGames$ = createEffect(() =>
    this.actions$.pipe(
      ofType(NHLCommands.loadGames),
      switchMap((action) => {
        const datePipe = new DatePipe('en-US');
        const formattedDate = datePipe.transform(action.date, 'yyyy-MM-dd');
        const params = formattedDate
          ? new HttpParams().set('date', formattedDate)
          : new HttpParams();
        return this.httpClient
          .get<{ list: Game[] }>(this.baseUrl + '/nhl/games', {
            params,
            responseType: 'json',
          })
          .pipe(
            map((response) => response.list),
            map((payload) => NHLDocuments.games({ payload })),
            catchError((error) => {
              return of(NHLCommands.loadGamesError({ error }));
            })
          );
      })
    )
  );
}

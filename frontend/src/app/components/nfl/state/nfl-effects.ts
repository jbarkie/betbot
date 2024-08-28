import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { environment } from '../../../../environments/environment';
import { NFLCommands, NFLDocuments } from './actions';
import { catchError, map, of, switchMap } from 'rxjs';
import { DatePipe } from '@angular/common';
import { Game } from '../../models';

@Injectable()
export class NflEffects {
  constructor(private actions$: Actions, private httpClient: HttpClient) {}

  readonly baseUrl = environment.apiUrl;

  loadGames$ = createEffect(() =>
    this.actions$.pipe(
      ofType(NFLCommands.loadGames),
      switchMap((action) => {
        const datePipe = new DatePipe('en-US');
        const formattedDate = datePipe.transform(action.date, 'yyyy-MM-dd');
        const params = formattedDate
          ? new HttpParams().set('date', formattedDate)
          : new HttpParams();
        return this.httpClient
          .get<{ list: Game[] }>(this.baseUrl + '/nfl/games', {
            params,
            responseType: 'json',
          })
          .pipe(
            map((response) => response.list),
            map((payload) => NFLDocuments.games({ payload })),
            catchError((error) => {
              return of(NFLCommands.loadGamesError({ error }));
            })
          );
      })
    )
  );
}

import { Injectable } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { HttpClient, HttpParams } from '@angular/common/http';
import { appActions } from '../../../state/actions';
import { catchError, map, of, switchMap } from 'rxjs';
import { NBADocuments, NbaCommands } from './actions';
import { Game } from '../../models';
import { DatePipe } from '@angular/common';

@Injectable()
export class NbaEffects {
  constructor(private actions$: Actions, private httpClient: HttpClient) {}

  readonly baseUrl = environment.apiUrl;
  onStartup = createEffect(() =>
    this.actions$.pipe(
      ofType(appActions.applicationStarted),
      map(() => NbaCommands.loadGames({ date: new Date() }))
    )
  );
  loadGames$ = createEffect(() =>
    this.actions$.pipe(
      ofType(NbaCommands.loadGames),
      switchMap((action) => {
        const datePipe = new DatePipe('en-US');
        const formattedDate = datePipe.transform(action.date, 'yyyy-MM-dd');
        const params = formattedDate ? new HttpParams().set('date', formattedDate) : new HttpParams();
        return this.httpClient.get<{ list: Game[] }>(this.baseUrl + '/nba/games', { params, responseType: 'json' }).pipe(
          map((response) => response.list),
          map((payload) => NBADocuments.games({ payload })),
          catchError((error) => {
            console.error('Error loading games:', error);
            return of(NBADocuments.games({ payload: [] })); 
          })
        );
      })
    )
  );
}

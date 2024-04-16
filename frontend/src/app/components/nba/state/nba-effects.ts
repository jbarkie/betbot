import { Injectable } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { HttpClient } from '@angular/common/http';
import { appActions } from '../../../state/actions';
import { map, switchMap } from 'rxjs';
import { NBADocuments, NbaCommands } from './actions';
import { Game } from '../../models';

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
        const date = action.date ? action.date.toISOString().split('T')[0] : '';
        return this.httpClient.get<{ list: Game[] }>(this.baseUrl + '/nba/games', { params: { date } }).pipe(
          map((results) => results.list),
          map((payload) => NBADocuments.games({ payload }))
        );
      })
    )
  );
}

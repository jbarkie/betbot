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
      map(() => NbaCommands.loadNBAGames())
    )
  );

  loadGames$ = createEffect(() =>
    this.actions$.pipe(
      ofType(NbaCommands.loadNBAGames),
      switchMap(() =>
        this.httpClient.get<{ list: Game[] }>(this.baseUrl + '/nba/games').pipe(
          map((results) => results.list),
          map((payload) => NBADocuments.games({ payload }))
        )
      )
    )
  );
}

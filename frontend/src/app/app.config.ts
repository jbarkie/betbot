import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideEffects } from '@ngrx/effects';
import { provideState, provideStore } from '@ngrx/store';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { routes } from './app.routes';
import { mlbFeature } from './components/mlb/state';
import { MlbEffects } from './components/mlb/state/mlb-effects';
import { nbaFeature } from './components/nba/state';
import { NbaEffects } from './components/nba/state/nba-effects';
import { nflFeature } from './components/nfl/state';
import { NflEffects } from './components/nfl/state/nfl-effects';
import { nhlFeature } from './components/nhl/state';
import { NhlEffects } from './components/nhl/state/nhl-effects';
import { authInterceptor } from './services/auth/auth.interceptor';
import { reducers } from './state';
import { AuthEffects } from './state/auth/auth.effects';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideStore(reducers),
    provideHttpClient(
      withInterceptors([authInterceptor])
    ),
    provideEffects([NbaEffects, MlbEffects, NhlEffects, NflEffects, AuthEffects]),
    provideState(nbaFeature),
    provideState(mlbFeature),
    provideState(nhlFeature),
    provideState(nflFeature),
    provideStoreDevtools()
  ],
};

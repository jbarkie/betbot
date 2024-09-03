import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideStore, provideState } from '@ngrx/store';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { reducers } from './state';
import { routes } from './app.routes';
import { HttpClientModule } from '@angular/common/http';
import { nbaFeature } from './components/nba/state';
import { provideEffects } from '@ngrx/effects';
import { NbaEffects } from './components/nba/state/nba-effects';
import { mlbFeature } from './components/mlb/state';
import { MlbEffects } from './components/mlb/state/mlb-effects';
import { authInterceptProvider } from './services/auth/auth.interceptor';
import { AuthEffects } from './state/auth/auth.effects';
import { NhlEffects } from './components/nhl/state/nhl-effects';
import { nhlFeature } from './components/nhl/state';
import { nflFeature } from './components/nfl/state';
import { NflEffects } from './components/nfl/state/nfl-effects';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideStore(reducers),
    importProvidersFrom(HttpClientModule),
    provideEffects([NbaEffects, MlbEffects, NhlEffects, NflEffects, AuthEffects]),
    provideState(nbaFeature),
    provideState(mlbFeature),
    provideState(nhlFeature),
    provideState(nflFeature),
    provideStoreDevtools(),
    authInterceptProvider
  ],
};

import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideStore } from '@ngrx/store';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { routes } from './app.routes';
import { authInterceptor } from './services/auth/auth.interceptor';
import {
  MLBStore,
  NBAStore,
  NFLStore,
  NHLStore,
} from './services/sports/sports.store';
import { reducers } from './state';
import { provideEffects } from '@ngrx/effects';
import { AuthEffects } from './state/auth/auth.effects';
import { AuthStore } from './services/auth/auth.store';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideStore(reducers),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideEffects([AuthEffects]),
    provideStoreDevtools(),
    provideHttpClientTesting(),
    AuthStore,
  ],
};

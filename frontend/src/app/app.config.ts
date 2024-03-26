import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideStore, provideState } from '@ngrx/store';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { reducers } from './state';

import { routes } from './app.routes';
import { provideHttpClient } from '@angular/common/http';
import { nbaFeature } from './components/nba/state';

export const appConfig: ApplicationConfig = {
  providers: [provideRouter(routes), provideStore(reducers), provideHttpClient(), provideState(nbaFeature), provideStoreDevtools()],
};

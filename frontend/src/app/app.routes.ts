import { Routes } from '@angular/router';
import { NbaComponent } from './components/nba/nba.component';
import { RegistrationComponent } from './components/registration/registration.component';
import { MlbComponent } from './components/mlb/mlb.component';
import { authGuard } from './services/auth/auth.guard';
import { NhlComponent } from './components/nhl/nhl.component';
import { NflComponent } from './components/nfl/nfl.component';
import {
  MLBStore,
  NBAStore,
  NFLStore,
  NHLStore,
} from './services/sports/sports.store';
import { HomeComponent } from './components/home/home.component';

export const routes: Routes = [
  {
    path: '',
    component: HomeComponent,
  },
  {
    path: 'register',
    component: RegistrationComponent,
  },
  {
    path: 'nba',
    component: NbaComponent,
    canActivate: [authGuard],
    providers: [NBAStore],
  },
  {
    path: 'mlb',
    component: MlbComponent,
    canActivate: [authGuard],
    providers: [MLBStore],
  },
  {
    path: 'nhl',
    component: NhlComponent,
    canActivate: [authGuard],
    providers: [NHLStore],
  },
  {
    path: 'nfl',
    component: NflComponent,
    canActivate: [authGuard],
    providers: [NFLStore],
  },
];

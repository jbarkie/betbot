import { Routes } from '@angular/router';
import { NbaComponent } from './components/nba/nba.component';
import { RegistrationComponent } from './components/registration/registration.component';
import { MlbComponent } from './components/mlb/mlb.component';
import { authGuard } from './services/auth/auth.guard';
import { NhlComponent } from './components/nhl/nhl.component';

export const routes: Routes = [
  {
    path: 'register',
    component: RegistrationComponent,
  },
  {
    path: 'nba',
    component: NbaComponent,
    canActivate: [authGuard],
  },
  {
    path: 'mlb',
    component: MlbComponent,
    canActivate: [authGuard],
  },
  {
    path: 'nhl',
    component: NhlComponent,
    canActivate: [authGuard],
  },
];

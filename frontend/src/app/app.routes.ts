import { Routes } from '@angular/router';
import { NbaComponent } from './components/nba/nba.component';
import { RegistrationComponent } from './components/registration/registration.component';
import { MlbComponent } from './components/mlb/mlb.component';
import { authGuard } from './services/auth/auth.guard';

export const routes: Routes = [
  {
    path: 'nba',
    component: NbaComponent,
    canActivate: [authGuard],
  },
  {
    path: 'register',
    component: RegistrationComponent,
  },
  {
    path: 'mlb',
    component: MlbComponent,
    canActivate: [authGuard],
  },
];

import { Routes } from '@angular/router';
import { NbaComponent } from './components/nba/nba.component';
import { RegistrationComponent } from './components/registration/registration.component';

export const routes: Routes = [
  {
    path: 'nba',
    component: NbaComponent,
  },
  {
    path: 'register',
    component: RegistrationComponent,
  }
];

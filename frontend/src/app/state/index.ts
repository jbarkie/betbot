import { ActionReducerMap } from '@ngrx/store';
import { authReducer, AuthState } from './auth/auth.reducer';
import { mlbFeature, MlbState } from '../components/mlb/state';
import { nbaFeature, NbaState } from '../components/nba/state';

export interface ApplicationState {
  auth: AuthState;
  mlb: MlbState;
  nba: NbaState;
}

export const reducers: ActionReducerMap<ApplicationState> = {
  auth: authReducer,
  mlb: mlbFeature.reducer,
  nba: nbaFeature.reducer,
};

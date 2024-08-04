import { ActionReducerMap } from '@ngrx/store';
import { authReducer, AuthState } from './auth/auth.reducer';

export interface ApplicationState {
    auth: AuthState;
}

export const reducers: ActionReducerMap<ApplicationState> = {
    auth: authReducer,
};

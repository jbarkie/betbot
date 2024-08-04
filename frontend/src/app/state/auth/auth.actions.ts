import { createActionGroup, emptyProps, props } from '@ngrx/store';

export const authActions = createActionGroup({
    source: 'Auth',
    events: {
        'Login Success': props<{ token: string }>(),
        'Login Failure': props<{ error: string }>(),
        'Logout': emptyProps(),
    }
});
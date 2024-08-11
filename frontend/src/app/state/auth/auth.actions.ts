import { createActionGroup, emptyProps, props } from '@ngrx/store';

export const authActions = createActionGroup({
    source: 'Auth',
    events: {
        'Register Success': props<{ token: string }>(),
        'Register Failure': props<{ error: string }>(),
        'Login Success': props<{ token: string }>(),
        'Login Failure': props<{ error: string }>(),
        'Logout': emptyProps(),
        'Show Login Modal': emptyProps(),
        'Hide Login Modal': emptyProps()
    }
});
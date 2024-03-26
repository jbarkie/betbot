import { createActionGroup, emptyProps } from '@ngrx/store';

export const appActions = createActionGroup({
    source: 'Application',
    events: {
        'Application Started': emptyProps(),
    }
})
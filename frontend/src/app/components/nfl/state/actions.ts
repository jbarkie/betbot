import { createActionGroup, props } from '@ngrx/store';
import { Game } from '../../models';

export const NFLCommands = createActionGroup({
    source: 'NFL Commands',
    events: {
        'Load Games': props<{ date: Date }>(),
        'Load Games Error': props<{ error: string }>(),
    },
});

export const NFLDocuments = createActionGroup({
    source: 'NFL Documents',
    events: {
        Games: props<{ payload: Game[] }>(),
    },
});
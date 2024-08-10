import { createActionGroup, props } from '@ngrx/store';
import { Game } from '../../models';

export const MLBCommands = createActionGroup({
    source: 'MLB Commands',
    events: {
        'Load Games': props<{ date: Date }>(),
        'Load Games Error': props<{ error: string }>(),
    }
})

export const MLBDocuments = createActionGroup({
    source: 'MLB Documents',
    events: {
        Games: props<{ payload: Game[] }>(),
    }
})
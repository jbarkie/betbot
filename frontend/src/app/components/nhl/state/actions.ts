import { createActionGroup, props } from '@ngrx/store';
import { Game } from '../../models';

export const NHLCommands = createActionGroup({
  source: 'NHL Commands',
  events: {
    'Load Games': props<{ date: Date }>(),
    'Load Games Error': props<{ error: string }>(),
  },
});

export const NHLDocuments = createActionGroup({
  source: 'NHL Documents',
  events: {
    Games: props<{ payload: Game[] }>(),
  },
});

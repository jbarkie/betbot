import { createActionGroup, props } from '@ngrx/store';
import { Game } from '../../models';

export const NBACommands = createActionGroup({
  source: 'NBA Commands',
  events: {
    'Load Games': props<{ date: Date }>(),
    'Load Games Error': props<{ error: string }>(),
  },
});

export const NBADocuments = createActionGroup({
  source: 'NBA Documents',
  events: {
    Games: props<{ payload: Game[] }>(),
  },
});

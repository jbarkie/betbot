import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { Game } from '../../models';

export const NbaCommands = createActionGroup({
  source: 'NBA Commands',
  events: {
    'Load Games': props<{ date?: Date }>(),
  },
});

export const NBADocuments = createActionGroup({
  source: 'NBA Documents',
  events: {
    Games: props<{ payload: Game[] }>(),
  },
});

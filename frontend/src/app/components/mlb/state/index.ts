import { createEntityAdapter } from '@ngrx/entity';
import { createFeature, createReducer, on, createSelector } from '@ngrx/store';
import { SportsState } from '../../sport-wrapper/state';
import { Game } from '../../models';
import { MLBCommands, MLBDocuments } from './actions';

export interface MlbState extends SportsState {}

const adapter = createEntityAdapter<Game>();
const initialState: MlbState = adapter.getInitialState({
  isLoaded: false,
  error: null,
});

export const mlbFeature = createFeature({
  name: 'mlb',
  reducer: createReducer(
    initialState,
    on(MLBDocuments.games, (s, a) =>
      adapter.setAll(a.payload, { ...s, isLoaded: true, error: null })
    ),
    on(MLBCommands.loadGamesError, (s, a) => ({
      ...s,
      isLoaded: true,
      error: a.error,
    }))
  ),
  extraSelectors: ({ selectMlbState }) => {
    const { selectAll } = adapter.getSelectors();
    const mlbArray = createSelector(selectMlbState, (s) => selectAll(s));
    return {
      selectMlbGames: createSelector(mlbArray, (games) =>
        games.map(
          (game) =>
            ({
              id: game.id,
              sport: game.sport,
              homeTeam: game.homeTeam,
              awayTeam: game.awayTeam,
              date: game.date,
              time: game.time,
              homeOdds: game.homeOdds,
              awayOdds: game.awayOdds,
            } as Game)
        )
      ),
      selectError: createSelector(selectMlbState, (s) => s.error ?? ''),
    };
  },
});

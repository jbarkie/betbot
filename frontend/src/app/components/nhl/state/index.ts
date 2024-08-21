import { createEntityAdapter } from '@ngrx/entity';
import { createFeature, createReducer, createSelector, on } from '@ngrx/store';
import { SportsState } from '../../sport-wrapper/state';
import { Game } from '../../models';
import { NHLCommands, NHLDocuments } from './actions';

export interface NhlState extends SportsState {}

const adapter = createEntityAdapter<Game>();
const initialState: NhlState = adapter.getInitialState({
  isLoaded: false,
  error: null,
});

export const nhlFeature = createFeature({
  name: 'nhl',
  reducer: createReducer(
    initialState,
    on(NHLDocuments.games, (s, a) =>
      adapter.setAll(a.payload, { ...s, isLoaded: true, error: null })
    ),
    on(NHLCommands.loadGamesError, (s, a) => ({
      ...s,
      isLoaded: true,
      error: a.error,
    }))
  ),
  extraSelectors: ({ selectNhlState }) => {
    const { selectAll } = adapter.getSelectors();
    const nhlArray = createSelector(selectNhlState, (s) => selectAll(s));
    return {
      selectNhlGames: createSelector(nhlArray, (games) =>
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
      selectError: createSelector(selectNhlState, (s) => s.error ?? ''),
    };
  },
});

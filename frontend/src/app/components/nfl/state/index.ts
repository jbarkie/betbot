import { SportsState } from '../../sport-wrapper/state';
import { createEntityAdapter } from '@ngrx/entity';
import { Game } from '../../models';
import { createFeature, createReducer, createSelector, on } from '@ngrx/store';
import { NFLCommands, NFLDocuments } from './actions';

export interface NflState extends SportsState {}

const adapter = createEntityAdapter<Game>();
const initialState: NflState = adapter.getInitialState({
  isLoaded: false,
  error: null,
});

export const nflFeature = createFeature({
  name: 'nfl',
  reducer: createReducer(
    initialState,
    on(NFLDocuments.games, (s, a) =>
      adapter.setAll(a.payload, { ...s, isLoaded: true, error: null })
    ),
    on(NFLCommands.loadGamesError, (s, a) => ({
      ...s,
      isLoaded: true,
      error: a.error,
    }))
  ),
  extraSelectors: ({ selectNflState }) => {
    const { selectAll } = adapter.getSelectors();
    const nflArray = createSelector(selectNflState, (s) => selectAll(s));
    return {
      selectNflGames: createSelector(nflArray, (games) =>
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
      selectError: createSelector(selectNflState, (s) => s.error ?? ''),
    };
  },
});

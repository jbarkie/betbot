import { EntityState, createEntityAdapter } from '@ngrx/entity';
import { Game } from '../../models';
import { createFeature, createReducer, createSelector, on } from '@ngrx/store';
import { NBADocuments, NbaCommands } from './actions';

export interface NbaState extends EntityState<Game> {
  isLoaded: boolean;
  error: any;
}

const adapter = createEntityAdapter<Game>();
const initialState: NbaState = adapter.getInitialState({
  isLoaded: false,
  error: null,
});

export const nbaFeature = createFeature({
  name: 'nba',
  reducer: createReducer(
    initialState,
    on(NBADocuments.games, (s, a) => adapter.setAll(a.payload, { ...s, isLoaded: true, error: null })),
    on(NbaCommands.loadGamesError, (s, a) => ({ ...s, isLoaded: true, error: a.error }))
  ),
  extraSelectors: ({ selectNbaState }) => {
    const { selectAll } = adapter.getSelectors();
    const nbaArray = createSelector(selectNbaState, (s) => selectAll(s));
    return {
      selectNbaGames: createSelector(nbaArray, (games) =>
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
      selectError: createSelector(selectNbaState, (s) => s.error),
    };
  },
});

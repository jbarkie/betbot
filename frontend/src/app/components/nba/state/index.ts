import { EntityState, createEntityAdapter } from '@ngrx/entity';
import { Game } from '../../models';
import { createFeature, createReducer, createSelector } from '@ngrx/store';

export interface NbaState extends EntityState<Game> {
  isLoaded: boolean;
}

const adapter = createEntityAdapter<Game>();
const initialState: NbaState = adapter.getInitialState({
  isLoaded: false,
});

export const nbaFeature = createFeature({
  name: 'nba',
  reducer: createReducer(initialState),
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
              odds: game.odds,
            } as Game)
        )
      ),
    };
  },
});

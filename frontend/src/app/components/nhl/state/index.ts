import { createEntityAdapter } from '@ngrx/entity';
import { createFeature, createReducer, on } from '@ngrx/store';
import { SportsState } from '../../sport-wrapper/state';
import { Game } from '../../models';
import { NHLDocuments } from './actions';

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
    )
  ),
});

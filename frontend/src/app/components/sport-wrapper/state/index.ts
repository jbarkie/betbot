import { EntityState } from "@ngrx/entity";
import { Game } from "../../models";

export interface SportsState extends EntityState<Game> {
    isLoaded: boolean;
    error: string | null;
}
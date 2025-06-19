from api.src.models.mlb_analytics import MlbAnalyticsResponse
from shared.database import connect_to_db
from api.src.models.tables import Odds
from machine_learning.data.models.mlb_models import MLBTeam


async def get_mlb_game_analytics(game_id: str):
    session = connect_to_db()
    game = session.query(Odds).filter_by(id=game_id).first()
    if not game:
        session.close()
        raise ValueError(f"Game with id {game_id} not found")

    # Get home and away team names
    home_team_name = game.home_team
    away_team_name = game.away_team

    # Get MLBTeam records for each team
    home_team = session.query(MLBTeam).filter_by(name=home_team_name).first()
    away_team = session.query(MLBTeam).filter_by(name=away_team_name).first()

    # Default to home team if data is missing
    predicted_winner = home_team_name
    win_probability = 0.5
    if home_team and away_team:
        if home_team.winning_percentage > away_team.winning_percentage:
            predicted_winner = home_team_name
            win_probability = 0.55
        elif away_team.winning_percentage > home_team.winning_percentage:
            predicted_winner = away_team_name
            win_probability = 0.55
        else:
            predicted_winner = home_team_name
            win_probability = 0.5

    session.close()
    return MlbAnalyticsResponse(
        id=game_id,
        home_team=home_team_name,
        away_team=away_team_name,
        predicted_winner=predicted_winner,
        win_probability=win_probability
    )
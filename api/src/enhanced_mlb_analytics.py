"""
Enhanced MLB Analytics Service

This module provides sophisticated game analysis using machine learning insights
from the machine_learning module, incorporating rolling statistics, momentum,
and advanced team metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from api.src.models.mlb_analytics import MlbAnalyticsResponse, TeamAnalytics
from shared.database import connect_to_db
from api.src.models.tables import Odds
from machine_learning.data.models.mlb_models import (
    MLBTeam, MLBOffensiveStats, MLBDefensiveStats, MLBSchedule
)


class EnhancedMLBAnalytics:
    """
    Enhanced MLB analytics service that incorporates machine learning insights
    for more sophisticated game predictions.
    """
    
    def __init__(self, rolling_window: int = 10):
        """
        Initialize the enhanced analytics service.
        
        Args:
            rolling_window: Number of games to include in rolling calculations
        """
        self.rolling_window = rolling_window
    
    async def get_enhanced_game_analytics(self, game_id: str) -> MlbAnalyticsResponse:
        """
        Get enhanced analytics for a specific MLB game.
        
        Args:
            game_id: ID of the game to analyze
            
        Returns:
            Enhanced analytics response with detailed insights
        """
        session = connect_to_db()
        
        try:
            # Get the game odds record
            game = session.query(Odds).filter_by(id=game_id).first()
            if not game:
                raise ValueError(f"Game with id {game_id} not found")
            
            # Get team names
            home_team_name = game.home_team
            away_team_name = game.away_team
            
            # Get team records
            home_team = session.query(MLBTeam).filter_by(name=home_team_name).first()
            away_team = session.query(MLBTeam).filter_by(name=away_team_name).first()
            
            if not home_team or not away_team:
                # Fallback to basic analysis if team data is missing
                return self._create_basic_response(game_id, home_team_name, away_team_name, home_team, away_team)
            
            # Calculate enhanced analytics
            home_analytics = self._calculate_team_analytics(session, home_team, game.time)
            away_analytics = self._calculate_team_analytics(session, away_team, game.time)
            
            # Determine prediction and confidence
            predicted_winner, win_probability, confidence_level, key_factors = self._make_prediction(
                home_analytics, away_analytics
            )
            
            return MlbAnalyticsResponse(
                id=game_id,
                home_team=home_team_name,
                away_team=away_team_name,
                predicted_winner=predicted_winner,
                win_probability=win_probability,
                home_analytics=home_analytics,
                away_analytics=away_analytics,
                key_factors=key_factors,
                confidence_level=confidence_level
            )
            
        finally:
            session.close()
    
    def _calculate_team_analytics(
        self, 
        session: Session, 
        team: MLBTeam, 
        game_time: datetime
    ) -> TeamAnalytics:
        """
        Calculate comprehensive analytics for a team.
        
        Args:
            session: Database session
            team: MLBTeam record
            game_time: Time of the game
            
        Returns:
            TeamAnalytics object with detailed metrics
        """
        # Get recent games for rolling calculations
        recent_games = self._get_recent_team_games(session, team.id, game_time)
        
        # Calculate rolling win percentage
        rolling_win_pct = self._calculate_rolling_win_percentage(recent_games, team.id)
        
        # Get offensive and defensive ratings
        offensive_rating = self._calculate_offensive_rating(session, team.id, game_time)
        defensive_rating = self._calculate_defensive_rating(session, team.id, game_time)
        
        # Calculate days of rest
        days_rest = self._calculate_days_rest(recent_games, game_time)
        
        # Calculate momentum score (combination of rolling stats and recent performance)
        momentum_score = self._calculate_momentum_score(rolling_win_pct, offensive_rating, defensive_rating)
        
        return TeamAnalytics(
            name=team.name,
            winning_percentage=team.winning_percentage,
            rolling_win_percentage=rolling_win_pct,
            offensive_rating=offensive_rating,
            defensive_rating=defensive_rating,
            days_rest=days_rest,
            momentum_score=momentum_score
        )
    
    def _get_recent_team_games(
        self, 
        session: Session, 
        team_id: int, 
        game_time: datetime,
        limit: int = None
    ) -> pd.DataFrame:
        """
        Get recent games for a team up to the specified time.
        
        Args:
            session: Database session
            team_id: ID of the team
            game_time: Cutoff time for games
            limit: Maximum number of games to retrieve
            
        Returns:
            DataFrame of recent games
        """
        if limit is None:
            limit = self.rolling_window * 2  # Get more games to ensure we have enough for rolling calculations
        
        games = session.query(MLBSchedule).filter(
            MLBSchedule.home_team_id == team_id,
            MLBSchedule.date < game_time.date(),
            MLBSchedule.status == 'Final'
        ).union(
            session.query(MLBSchedule).filter(
                MLBSchedule.away_team_id == team_id,
                MLBSchedule.date < game_time.date(),
                MLBSchedule.status == 'Final'
            )
        ).order_by(MLBSchedule.date.desc()).limit(limit).all()
        
        # Convert to DataFrame for easier manipulation
        games_data = []
        for game in games:
            games_data.append({
                'date': game.date,
                'home_team_id': game.home_team_id,
                'away_team_id': game.away_team_id,
                'home_score': game.home_score,
                'away_score': game.away_score
            })
        
        return pd.DataFrame(games_data)
    
    def _calculate_rolling_win_percentage(self, games_df: pd.DataFrame, team_id: int) -> Optional[float]:
        """
        Calculate rolling win percentage for the last N games.
        
        Args:
            games_df: DataFrame of team games
            team_id: ID of the team
            
        Returns:
            Rolling win percentage or None if insufficient data
        """
        if len(games_df) < self.rolling_window:
            return None
        
        # Take the most recent games
        recent_games = games_df.head(self.rolling_window)
        
        # Calculate wins
        wins = 0
        for _, game in recent_games.iterrows():
            if game['home_team_id'] == team_id:
                if game['home_score'] > game['away_score']:
                    wins += 1
            else:  # away_team_id == team_id
                if game['away_score'] > game['home_score']:
                    wins += 1
        
        return round(wins / self.rolling_window, 3)
    
    def _calculate_offensive_rating(self, session: Session, team_id: int, game_time: datetime) -> Optional[float]:
        """
        Calculate offensive rating based on recent offensive statistics.
        
        Args:
            session: Database session
            team_id: ID of the team
            game_time: Time of the game
            
        Returns:
            Offensive rating or None if no data available
        """
        # Get most recent offensive stats
        offensive_stats = session.query(MLBOffensiveStats).filter(
            MLBOffensiveStats.team_id == team_id,
            MLBOffensiveStats.date <= game_time.date()
        ).order_by(MLBOffensiveStats.date.desc()).first()
        
        if not offensive_stats:
            return None
        
        # Simple offensive rating combining key metrics
        # Weighted combination of batting average, OBP, and SLG
        offensive_rating = (
            offensive_stats.team_batting_average * 0.3 +
            offensive_stats.on_base_percentage * 0.4 +
            offensive_stats.slugging_percentage * 0.3
        )
        
        return round(offensive_rating, 3)
    
    def _calculate_defensive_rating(self, session: Session, team_id: int, game_time: datetime) -> Optional[float]:
        """
        Calculate defensive rating based on recent defensive statistics.
        
        Args:
            session: Database session
            team_id: ID of the team
            game_time: Time of the game
            
        Returns:
            Defensive rating or None if no data available
        """
        # Get most recent defensive stats
        defensive_stats = session.query(MLBDefensiveStats).filter(
            MLBDefensiveStats.team_id == team_id,
            MLBDefensiveStats.date <= game_time.date()
        ).order_by(MLBDefensiveStats.date.desc()).first()
        
        if not defensive_stats:
            return None
        
        # Simple defensive rating (lower ERA and WHIP are better)
        # Convert to a positive scale where higher is better
        era_component = max(0, 6.0 - defensive_stats.team_era) / 6.0  # Normalize ERA
        whip_component = max(0, 2.0 - defensive_stats.whip) / 2.0    # Normalize WHIP
        
        defensive_rating = (era_component * 0.6 + whip_component * 0.4)
        
        return round(defensive_rating, 3)
    
    def _calculate_days_rest(self, games_df: pd.DataFrame, game_time: datetime) -> Optional[int]:
        """
        Calculate days of rest since the last game.
        
        Args:
            games_df: DataFrame of team games
            game_time: Time of the upcoming game
            
        Returns:
            Number of days of rest or None if no recent games
        """
        if games_df.empty:
            return None
        
        # Get the most recent game date
        most_recent_game = games_df.iloc[0]['date']
        
        # Calculate days between most recent game and upcoming game
        days_rest = (game_time.date() - most_recent_game).days
        
        return days_rest
    
    def _calculate_momentum_score(
        self, 
        rolling_win_pct: Optional[float], 
        offensive_rating: Optional[float], 
        defensive_rating: Optional[float]
    ) -> Optional[float]:
        """
        Calculate a momentum score combining multiple factors.
        
        Args:
            rolling_win_pct: Rolling win percentage
            offensive_rating: Offensive rating
            defensive_rating: Defensive rating
            
        Returns:
            Momentum score or None if insufficient data
        """
        scores = []
        weights = []
        
        if rolling_win_pct is not None:
            scores.append(rolling_win_pct)
            weights.append(0.5)
        
        if offensive_rating is not None:
            scores.append(offensive_rating)
            weights.append(0.25)
        
        if defensive_rating is not None:
            scores.append(defensive_rating)
            weights.append(0.25)
        
        if not scores:
            return None
        
        # Weighted average of available scores
        momentum_score = sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)
        
        return round(momentum_score, 3)
    
    def _make_prediction(
        self, 
        home_analytics: TeamAnalytics, 
        away_analytics: TeamAnalytics
    ) -> Tuple[str, float, str, Dict[str, str]]:
        """
        Make prediction based on team analytics.
        
        Args:
            home_analytics: Home team analytics
            away_analytics: Away team analytics
            
        Returns:
            Tuple of (predicted_winner, win_probability, confidence_level, key_factors)
        """
        key_factors = {}
        home_advantages = 0
        away_advantages = 0
        
        # Compare basic winning percentages
        if home_analytics.winning_percentage > away_analytics.winning_percentage:
            home_advantages += 1
            key_factors["season_record"] = f"{home_analytics.name} has better season record"
        else:
            away_advantages += 1
            key_factors["season_record"] = f"{away_analytics.name} has better season record"
        
        # Compare momentum (rolling win percentage)
        if home_analytics.rolling_win_percentage and away_analytics.rolling_win_percentage:
            if home_analytics.rolling_win_percentage > away_analytics.rolling_win_percentage:
                home_advantages += 1
                key_factors["momentum"] = f"{home_analytics.name} has better recent form"
            else:
                away_advantages += 1
                key_factors["momentum"] = f"{away_analytics.name} has better recent form"
        
        # Compare offensive ratings
        if home_analytics.offensive_rating and away_analytics.offensive_rating:
            if home_analytics.offensive_rating > away_analytics.offensive_rating:
                home_advantages += 1
                key_factors["offense"] = f"{home_analytics.name} has stronger offense"
            else:
                away_advantages += 1
                key_factors["offense"] = f"{away_analytics.name} has stronger offense"
        
        # Compare defensive ratings
        if home_analytics.defensive_rating and away_analytics.defensive_rating:
            if home_analytics.defensive_rating > away_analytics.defensive_rating:
                home_advantages += 1
                key_factors["defense"] = f"{home_analytics.name} has stronger defense"
            else:
                away_advantages += 1
                key_factors["defense"] = f"{away_analytics.name} has stronger defense"
        
        # Rest advantage
        if home_analytics.days_rest is not None and away_analytics.days_rest is not None:
            rest_difference = home_analytics.days_rest - away_analytics.days_rest
            if abs(rest_difference) >= 2:  # Significant rest difference
                if rest_difference > 0:
                    home_advantages += 1
                    key_factors["rest"] = f"{home_analytics.name} has rest advantage ({home_analytics.days_rest} vs {away_analytics.days_rest} days)"
                else:
                    away_advantages += 1
                    key_factors["rest"] = f"{away_analytics.name} has rest advantage ({away_analytics.days_rest} vs {home_analytics.days_rest} days)"
        
        # Determine winner and probability
        total_comparisons = len([k for k in key_factors.keys() if k != "rest"]) + (1 if "rest" in key_factors else 0)
        
        if total_comparisons == 0:
            # Fallback to basic prediction
            if home_analytics.winning_percentage > away_analytics.winning_percentage:
                predicted_winner = home_analytics.name
                win_probability = 0.55
                confidence_level = "Low"
            else:
                predicted_winner = away_analytics.name
                win_probability = 0.55
                confidence_level = "Low"
        else:
            home_score = home_advantages / total_comparisons
            
            if home_score > 0.6:
                predicted_winner = home_analytics.name
                win_probability = 0.55 + (home_score - 0.5) * 0.3  # Scale probability
                confidence_level = "High"
            elif home_score < 0.4:
                predicted_winner = away_analytics.name
                win_probability = 0.55 + (0.5 - home_score) * 0.3
                confidence_level = "High"
            else:
                predicted_winner = home_analytics.name if home_score >= 0.5 else away_analytics.name
                win_probability = 0.52
                confidence_level = "Medium"
        
        # Ensure probability stays within reasonable bounds
        win_probability = max(0.45, min(0.75, win_probability))
        
        return predicted_winner, round(win_probability, 3), confidence_level, key_factors
    
    def _create_basic_response(
        self, 
        game_id: str, 
        home_team_name: str, 
        away_team_name: str, 
        home_team: Optional[MLBTeam], 
        away_team: Optional[MLBTeam]
    ) -> MlbAnalyticsResponse:
        """
        Create a basic response when enhanced data is not available.
        
        Args:
            game_id: Game ID
            home_team_name: Home team name
            away_team_name: Away team name
            home_team: Home team record (may be None)
            away_team: Away team record (may be None)
            
        Returns:
            Basic analytics response
        """
        predicted_winner = home_team_name
        win_probability = 0.5
        
        if home_team and away_team:
            if home_team.winning_percentage > away_team.winning_percentage:
                predicted_winner = home_team_name
                win_probability = 0.55
            elif away_team.winning_percentage > home_team.winning_percentage:
                predicted_winner = away_team_name
                win_probability = 0.55
        
        return MlbAnalyticsResponse(
            id=game_id,
            home_team=home_team_name,
            away_team=away_team_name,
            predicted_winner=predicted_winner,
            win_probability=win_probability,
            confidence_level="Low"
        )


# Convenience function for backward compatibility
async def get_enhanced_mlb_game_analytics(game_id: str) -> MlbAnalyticsResponse:
    """
    Get enhanced MLB game analytics using the new analytics service.
    
    Args:
        game_id: ID of the game to analyze
        
    Returns:
        Enhanced analytics response
    """
    analytics_service = EnhancedMLBAnalytics()
    return await analytics_service.get_enhanced_game_analytics(game_id)

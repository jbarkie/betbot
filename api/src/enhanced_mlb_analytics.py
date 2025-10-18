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
from api.src.ml_model_service import get_mlb_model_service
from api.src.ml_config import MLB_REQUIRED_FEATURES


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

            # Try ML prediction first, fallback to rule-based
            ml_prediction = self._try_ml_prediction(session, home_team, away_team, home_analytics, away_analytics, game.time)

            if ml_prediction:
                # Use ML prediction
                predicted_winner_type, win_probability, ml_metadata = ml_prediction
                predicted_winner = home_team_name if predicted_winner_type == 'home' else away_team_name

                # Get key factors from rule-based system for explainability
                _, _, _, key_factors = self._make_rule_based_prediction(home_analytics, away_analytics)

                return MlbAnalyticsResponse(
                    id=game_id,
                    home_team=home_team_name,
                    away_team=away_team_name,
                    predicted_winner=predicted_winner,
                    win_probability=win_probability,
                    home_analytics=home_analytics,
                    away_analytics=away_analytics,
                    key_factors=key_factors,
                    confidence_level=ml_metadata['model_confidence'],
                    ml_model_name=ml_metadata['ml_model_name'],
                    ml_confidence=ml_metadata['model_confidence'],
                    home_win_probability=ml_metadata['home_win_probability'],
                    away_win_probability=ml_metadata['away_win_probability'],
                    prediction_method='machine_learning',
                    feature_importance=ml_metadata.get('feature_importance')
                )
            else:
                # Fallback to rule-based prediction
                predicted_winner, win_probability, confidence_level, key_factors = self._make_rule_based_prediction(
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
                    confidence_level=confidence_level,
                    prediction_method='rule_based'
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
    
    def _try_ml_prediction(
        self,
        session: Session,
        home_team: MLBTeam,
        away_team: MLBTeam,
        home_analytics: TeamAnalytics,
        away_analytics: TeamAnalytics,
        game_time: datetime
    ) -> Optional[Tuple[str, float, Dict]]:
        """
        Attempt to make a prediction using the ML model.

        Args:
            session: Database session
            home_team: Home team record
            away_team: Away team record
            home_analytics: Home team analytics
            away_analytics: Away team analytics
            game_time: Game time

        Returns:
            Tuple of (predicted_winner_type, win_probability, metadata) or None if ML prediction fails
        """
        try:
            # Get the ML model service
            ml_service = get_mlb_model_service()

            if not ml_service.is_available:
                return None

            # Prepare features for ML model
            features = self._prepare_ml_features(
                session, home_team, away_team, home_analytics, away_analytics, game_time
            )

            if not features:
                return None

            # Get prediction from ML model
            prediction_result = ml_service.predict(features)

            if not prediction_result:
                return None

            predicted_winner_type, win_probability, metadata = prediction_result

            # Only use ML prediction if confidence is sufficient
            if metadata.get('use_ml_prediction', False):
                return predicted_winner_type, win_probability, metadata
            else:
                return None

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"ML prediction failed: {e}")
            return None

    def _prepare_ml_features(
        self,
        session: Session,
        home_team: MLBTeam,
        away_team: MLBTeam,
        home_analytics: TeamAnalytics,
        away_analytics: TeamAnalytics,
        game_time: datetime
    ) -> Optional[Dict[str, float]]:
        """
        Prepare features for ML model prediction.

        Args:
            session: Database session
            home_team: Home team record
            away_team: Away team record
            home_analytics: Home team analytics
            away_analytics: Away team analytics
            game_time: Game time

        Returns:
            Dictionary of features or None if features cannot be prepared
        """
        try:
            # Get recent games for rolling stats (already calculated in analytics)
            home_recent_games = self._get_recent_team_games(session, home_team.id, game_time)
            away_recent_games = self._get_recent_team_games(session, away_team.id, game_time)

            # Calculate rolling runs scored/allowed
            home_rolling_runs_scored = home_recent_games['home_score'].where(
                home_recent_games['home_team_id'] == home_team.id,
                home_recent_games['away_score']
            ).head(10).mean() if not home_recent_games.empty else 0.0

            home_rolling_runs_allowed = home_recent_games['away_score'].where(
                home_recent_games['home_team_id'] == home_team.id,
                home_recent_games['home_score']
            ).head(10).mean() if not home_recent_games.empty else 0.0

            away_rolling_runs_scored = away_recent_games['home_score'].where(
                away_recent_games['home_team_id'] == away_team.id,
                away_recent_games['away_score']
            ).head(10).mean() if not away_recent_games.empty else 0.0

            away_rolling_runs_allowed = away_recent_games['away_score'].where(
                away_recent_games['home_team_id'] == away_team.id,
                away_recent_games['home_score']
            ).head(10).mean() if not away_recent_games.empty else 0.0

            # Get head-to-head stats
            h2h_stats = self._get_head_to_head_stats(session, home_team.id, away_team.id, game_time)

            # Get recent offensive/defensive stats
            home_offensive = session.query(MLBOffensiveStats).filter(
                MLBOffensiveStats.team_id == home_team.id,
                MLBOffensiveStats.date <= game_time.date()
            ).order_by(MLBOffensiveStats.date.desc()).first()

            away_offensive = session.query(MLBOffensiveStats).filter(
                MLBOffensiveStats.team_id == away_team.id,
                MLBOffensiveStats.date <= game_time.date()
            ).order_by(MLBOffensiveStats.date.desc()).first()

            home_defensive = session.query(MLBDefensiveStats).filter(
                MLBDefensiveStats.team_id == home_team.id,
                MLBDefensiveStats.date <= game_time.date()
            ).order_by(MLBDefensiveStats.date.desc()).first()

            away_defensive = session.query(MLBDefensiveStats).filter(
                MLBDefensiveStats.team_id == away_team.id,
                MLBDefensiveStats.date <= game_time.date()
            ).order_by(MLBDefensiveStats.date.desc()).first()

            # Prepare feature dictionary
            features = {
                'home_rolling_win_pct': home_analytics.rolling_win_percentage or 0.0,
                'away_rolling_win_pct': away_analytics.rolling_win_percentage or 0.0,
                'home_rolling_runs_scored': float(home_rolling_runs_scored),
                'away_rolling_runs_scored': float(away_rolling_runs_scored),
                'home_rolling_runs_allowed': float(home_rolling_runs_allowed),
                'away_rolling_runs_allowed': float(away_rolling_runs_allowed),
                'home_days_rest': float(home_analytics.days_rest or 1),
                'away_days_rest': float(away_analytics.days_rest or 1),
                'home_batting_avg': float(home_offensive.team_batting_average if home_offensive else 0.25),
                'away_batting_avg': float(away_offensive.team_batting_average if away_offensive else 0.25),
                'home_obp': float(home_offensive.on_base_percentage if home_offensive else 0.32),
                'away_obp': float(away_offensive.on_base_percentage if away_offensive else 0.32),
                'home_slg': float(home_offensive.slugging_percentage if home_offensive else 0.4),
                'away_slg': float(away_offensive.slugging_percentage if away_offensive else 0.4),
                'home_era': float(home_defensive.team_era if home_defensive else 4.5),
                'away_era': float(away_defensive.team_era if away_defensive else 4.5),
                'home_whip': float(home_defensive.whip if home_defensive else 1.35),
                'away_whip': float(away_defensive.whip if away_defensive else 1.35),
                'home_strikeouts': float(home_defensive.strikeouts if home_defensive else 150),
                'away_strikeouts': float(away_defensive.strikeouts if away_defensive else 150),
                'h2h_home_win_pct': h2h_stats['home_win_pct'],
                'h2h_away_win_pct': h2h_stats['away_win_pct'],
                'h2h_games_played': float(h2h_stats['games_played']),
                'month': float(game_time.month),
                'day_of_week': float(game_time.weekday()),
                'is_weekend': float(1 if game_time.weekday() >= 5 else 0)
            }

            return features

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Feature preparation failed: {e}")
            return None

    def _get_head_to_head_stats(
        self,
        session: Session,
        home_team_id: int,
        away_team_id: int,
        game_time: datetime,
        window: int = 5
    ) -> Dict[str, float]:
        """Get head-to-head statistics between two teams."""
        h2h_games = session.query(MLBSchedule).filter(
            (
                ((MLBSchedule.home_team_id == home_team_id) & (MLBSchedule.away_team_id == away_team_id)) |
                ((MLBSchedule.home_team_id == away_team_id) & (MLBSchedule.away_team_id == home_team_id))
            ),
            MLBSchedule.date < game_time.date(),
            MLBSchedule.status == 'Final'
        ).order_by(MLBSchedule.date.desc()).limit(window).all()

        if not h2h_games:
            return {'home_win_pct': 0.0, 'away_win_pct': 0.0, 'games_played': 0}

        home_wins = sum(
            1 for game in h2h_games
            if (game.home_team_id == home_team_id and game.home_score > game.away_score) or
               (game.away_team_id == home_team_id and game.away_score > game.home_score)
        )

        games_played = len(h2h_games)

        return {
            'home_win_pct': round(home_wins / games_played, 3),
            'away_win_pct': round((games_played - home_wins) / games_played, 3),
            'games_played': games_played
        }

    def _make_rule_based_prediction(
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
            confidence_level="Low",
            prediction_method="rule_based"
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

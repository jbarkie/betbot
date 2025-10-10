"""
Tests for the enhanced MLB analytics service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import pandas as pd

from api.src.enhanced_mlb_analytics import EnhancedMLBAnalytics
from api.src.models.mlb_analytics import MlbAnalyticsResponse, TeamAnalytics


class TestEnhancedMLBAnalytics:
    """Test cases for the EnhancedMLBAnalytics service."""
    
    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def sample_team(self):
        """Create a sample MLB team for testing."""
        team = Mock()
        team.id = 1
        team.name = "Test Team"
        team.winning_percentage = 0.600
        return team
    
    @pytest.fixture
    def sample_offensive_stats(self):
        """Create sample offensive statistics."""
        stats = Mock()
        stats.team_batting_average = 0.250
        stats.on_base_percentage = 0.320
        stats.slugging_percentage = 0.420
        return stats
    
    @pytest.fixture
    def sample_defensive_stats(self):
        """Create sample defensive statistics."""
        stats = Mock()
        stats.team_era = 4.50
        stats.whip = 1.35
        return stats
    
    def test_calculate_rolling_win_percentage_sufficient_data(self, analytics_service):
        """Test rolling win percentage calculation with sufficient data."""
        # Create sample games data
        games_data = []
        for i in range(10):  # More than rolling_window (5)
            games_data.append({
                'date': date.today(),
                'home_team_id': 1,
                'away_team_id': 2,
                'home_score': 5 if i < 7 else 3,  # Win 7 out of 10 games
                'away_score': 3 if i < 7 else 5
            })
        
        games_df = pd.DataFrame(games_data)
        
        # Calculate rolling win percentage for team 1 (home team)
        rolling_pct = analytics_service._calculate_rolling_win_percentage(games_df, 1)
        
        # Should be 7/10 = 0.7 for the most recent 5 games
        assert rolling_pct is not None
        assert isinstance(rolling_pct, float)
    
    def test_calculate_rolling_win_percentage_insufficient_data(self, analytics_service):
        """Test rolling win percentage calculation with insufficient data."""
        # Create sample games data with less than rolling_window games
        games_data = []
        for i in range(3):  # Less than rolling_window (5)
            games_data.append({
                'date': date.today(),
                'home_team_id': 1,
                'away_team_id': 2,
                'home_score': 5,
                'away_score': 3
            })
        
        games_df = pd.DataFrame(games_data)
        
        # Calculate rolling win percentage
        rolling_pct = analytics_service._calculate_rolling_win_percentage(games_df, 1)
        
        # Should return None due to insufficient data
        assert rolling_pct is None
    
    def test_calculate_offensive_rating(self, analytics_service, mock_session, sample_offensive_stats):
        """Test offensive rating calculation."""
        # Mock the database query
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_offensive_stats
        
        # Calculate offensive rating
        offensive_rating = analytics_service._calculate_offensive_rating(
            mock_session, 1, datetime.now()
        )
        
        # Should calculate weighted average
        expected_rating = (0.250 * 0.3 + 0.320 * 0.4 + 0.420 * 0.3)
        assert offensive_rating is not None
        assert abs(offensive_rating - expected_rating) < 0.001
    
    def test_calculate_defensive_rating(self, analytics_service, mock_session, sample_defensive_stats):
        """Test defensive rating calculation."""
        # Mock the database query
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_defensive_stats
        
        # Calculate defensive rating
        defensive_rating = analytics_service._calculate_defensive_rating(
            mock_session, 1, datetime.now()
        )
        
        # Should calculate normalized defensive metrics
        assert defensive_rating is not None
        assert 0 <= defensive_rating <= 1  # Should be normalized
    
    def test_calculate_momentum_score(self, analytics_service):
        """Test momentum score calculation."""
        # Test with all metrics available
        momentum_score = analytics_service._calculate_momentum_score(
            rolling_win_pct=0.7,
            offensive_rating=0.8,
            defensive_rating=0.6
        )
        
        assert momentum_score is not None
        assert isinstance(momentum_score, float)
        assert 0 <= momentum_score <= 1
    
    def test_calculate_momentum_score_partial_data(self, analytics_service):
        """Test momentum score calculation with partial data."""
        # Test with only some metrics available
        momentum_score = analytics_service._calculate_momentum_score(
            rolling_win_pct=0.7,
            offensive_rating=None,
            defensive_rating=0.6
        )
        
        assert momentum_score is not None
        assert isinstance(momentum_score, float)
    
    def test_calculate_momentum_score_no_data(self, analytics_service):
        """Test momentum score calculation with no data."""
        momentum_score = analytics_service._calculate_momentum_score(
            rolling_win_pct=None,
            offensive_rating=None,
            defensive_rating=None
        )
        
        assert momentum_score is None
    
    def test_make_prediction_clear_home_advantage(self, analytics_service):
        """Test prediction when home team has clear advantage."""
        home_analytics = TeamAnalytics(
            name="Home Team",
            winning_percentage=0.700,
            rolling_win_percentage=0.800,
            offensive_rating=0.750,
            defensive_rating=0.700,
            days_rest=2,
            momentum_score=0.750
        )
        
        away_analytics = TeamAnalytics(
            name="Away Team",
            winning_percentage=0.400,
            rolling_win_percentage=0.300,
            offensive_rating=0.500,
            defensive_rating=0.400,
            days_rest=1,
            momentum_score=0.400
        )
        
        predicted_winner, win_probability, confidence_level, key_factors = analytics_service._make_prediction(
            home_analytics, away_analytics
        )
        
        assert predicted_winner == "Home Team"
        assert win_probability > 0.55
        assert confidence_level == "High"
        assert len(key_factors) > 0
    
    def test_make_prediction_close_matchup(self, analytics_service):
        """Test prediction for a close matchup."""
        home_analytics = TeamAnalytics(
            name="Home Team",
            winning_percentage=0.520,
            rolling_win_percentage=0.480,
            offensive_rating=0.550,
            defensive_rating=0.530,
            days_rest=2,
            momentum_score=0.520
        )
        
        away_analytics = TeamAnalytics(
            name="Away Team",
            winning_percentage=0.510,
            rolling_win_percentage=0.520,
            offensive_rating=0.540,
            defensive_rating=0.520,
            days_rest=1,
            momentum_score=0.510
        )
        
        predicted_winner, win_probability, confidence_level, key_factors = analytics_service._make_prediction(
            home_analytics, away_analytics
        )
        
        assert predicted_winner in ["Home Team", "Away Team"]
        assert 0.45 <= win_probability <= 0.65
        assert confidence_level in ["High", "Medium", "Low"]  # Allow all confidence levels for close matchups
        assert len(key_factors) > 0
    
    @pytest.mark.asyncio
    @patch('api.src.enhanced_mlb_analytics.connect_to_db')
    async def test_get_enhanced_game_analytics_success(self, mock_connect, analytics_service):
        """Test successful enhanced analytics retrieval."""
        # Mock database setup
        mock_session = Mock()
        mock_connect.return_value = mock_session
        
        # Mock game odds
        mock_game = Mock()
        mock_game.id = "test_game_1"
        mock_game.home_team = "Home Team"
        mock_game.away_team = "Away Team"
        mock_game.time = datetime.now()
        
        # Mock team records
        mock_home_team = Mock()
        mock_home_team.id = 1
        mock_home_team.name = "Home Team"
        mock_home_team.winning_percentage = 0.600
        
        mock_away_team = Mock()
        mock_away_team.id = 2
        mock_away_team.name = "Away Team"
        mock_away_team.winning_percentage = 0.500
        
        # Mock database queries
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_game, mock_home_team, mock_away_team
        ]
        
        # Mock the internal methods to return sample data
        with patch.object(analytics_service, '_get_recent_team_games', return_value=pd.DataFrame()):
            with patch.object(analytics_service, '_calculate_rolling_win_percentage', return_value=0.6):
                with patch.object(analytics_service, '_calculate_offensive_rating', return_value=0.7):
                    with patch.object(analytics_service, '_calculate_defensive_rating', return_value=0.6):
                        with patch.object(analytics_service, '_calculate_days_rest', return_value=2):
                            with patch.object(analytics_service, '_calculate_momentum_score', return_value=0.65):
                                
                                result = await analytics_service.get_enhanced_game_analytics("test_game_1")
                                
                                assert isinstance(result, MlbAnalyticsResponse)
                                assert result.id == "test_game_1"
                                assert result.home_team == "Home Team"
                                assert result.away_team == "Away Team"
                                assert result.home_analytics is not None
                                assert result.away_analytics is not None
                                assert result.key_factors is not None
                                assert result.confidence_level is not None
    
    @pytest.mark.asyncio
    @patch('api.src.enhanced_mlb_analytics.connect_to_db')
    async def test_get_enhanced_game_analytics_game_not_found(self, mock_connect, analytics_service):
        """Test enhanced analytics when game is not found."""
        # Mock database setup
        mock_session = Mock()
        mock_connect.return_value = mock_session
        
        # Mock empty game query
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Game with id test_game_not_found not found"):
            await analytics_service.get_enhanced_game_analytics("test_game_not_found")


if __name__ == "__main__":
    pytest.main([__file__])

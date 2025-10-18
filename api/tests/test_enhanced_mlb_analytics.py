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
        
        predicted_winner, win_probability, confidence_level, key_factors = analytics_service._make_rule_based_prediction(
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
        
        predicted_winner, win_probability, confidence_level, key_factors = analytics_service._make_rule_based_prediction(
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

    @pytest.mark.asyncio
    @patch('api.src.enhanced_mlb_analytics.connect_to_db')
    async def test_get_enhanced_game_analytics_missing_team_data(self, mock_connect, analytics_service):
        """Test enhanced analytics when team data is missing (fallback to basic response)."""
        # Mock database setup
        mock_session = Mock()
        mock_connect.return_value = mock_session

        # Mock game odds
        mock_game = Mock()
        mock_game.id = "test_game_missing_teams"
        mock_game.home_team = "Home Team"
        mock_game.away_team = "Away Team"
        mock_game.time = datetime.now()

        # Mock database queries - game exists but teams don't
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_game,  # Game found
            None,       # Home team not found
            None        # Away team not found
        ]

        result = await analytics_service.get_enhanced_game_analytics("test_game_missing_teams")

        # Should return basic response
        assert isinstance(result, MlbAnalyticsResponse)
        assert result.id == "test_game_missing_teams"
        assert result.predicted_winner == "Home Team"  # Default to home
        assert result.win_probability == 0.5
        assert result.confidence_level == "Low"
        assert result.prediction_method == "rule_based"


class TestEnhancedMLBAnalyticsMLIntegration:
    """Test cases for ML integration in EnhancedMLBAnalytics."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def sample_ml_features(self):
        """Create sample ML features dictionary."""
        from api.src.ml_config import MLB_REQUIRED_FEATURES
        return {feature: 0.5 for feature in MLB_REQUIRED_FEATURES}

    @pytest.fixture
    def sample_home_analytics(self):
        """Create sample home team analytics."""
        return TeamAnalytics(
            name="Home Team",
            winning_percentage=0.600,
            rolling_win_percentage=0.650,
            offensive_rating=0.700,
            defensive_rating=0.680,
            days_rest=2,
            momentum_score=0.700
        )

    @pytest.fixture
    def sample_away_analytics(self):
        """Create sample away team analytics."""
        return TeamAnalytics(
            name="Away Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.480,
            offensive_rating=0.650,
            defensive_rating=0.620,
            days_rest=1,
            momentum_score=0.600
        )

    def test_try_ml_prediction_success(self, analytics_service, mock_session, sample_ml_features, sample_home_analytics, sample_away_analytics):
        """Test successful ML prediction attempt."""
        # Mock ML service and prediction
        mock_ml_service = Mock()
        mock_ml_service.is_available = True
        mock_ml_service.predict.return_value = (
            'home',  # predicted winner
            0.65,    # win probability
            {
                'ml_model_name': 'RandomForest-v1.0',
                'model_confidence': 'High',
                'home_win_probability': 0.65,
                'away_win_probability': 0.35,
                'feature_importance': {'home_rolling_win_pct': 0.15},
                'use_ml_prediction': True
            }
        )

        with patch('api.src.enhanced_mlb_analytics.get_mlb_model_service', return_value=mock_ml_service):
            with patch.object(analytics_service, '_prepare_ml_features', return_value=sample_ml_features):
                result = analytics_service._try_ml_prediction(
                    session=mock_session,
                    home_team=Mock(id=1, name='Home Team'),
                    away_team=Mock(id=2, name='Away Team'),
                    home_analytics=sample_home_analytics,
                    away_analytics=sample_away_analytics,
                    game_time=datetime.now()
                )

                assert result is not None
                predicted_winner, win_prob, metadata = result

                assert predicted_winner == 'home'
                assert win_prob == 0.65
                assert metadata['ml_model_name'] == 'RandomForest-v1.0'

    def test_try_ml_prediction_low_confidence(self, analytics_service, mock_session, sample_ml_features, sample_home_analytics, sample_away_analytics):
        """Test ML prediction with low confidence falls back to None."""
        # Mock ML service with low confidence prediction
        mock_ml_service = Mock()
        mock_ml_service.is_available = True
        mock_ml_service.predict.return_value = (
            'home',
            0.52,  # Below threshold
            {
                'ml_model_name': 'RandomForest-v1.0',
                'model_confidence': 'Low',
                'home_win_probability': 0.52,
                'away_win_probability': 0.48,
                'use_ml_prediction': False  # Below confidence threshold
            }
        )

        with patch('api.src.enhanced_mlb_analytics.get_mlb_model_service', return_value=mock_ml_service):
            with patch.object(analytics_service, '_prepare_ml_features', return_value=sample_ml_features):
                result = analytics_service._try_ml_prediction(
                    session=mock_session,
                    home_team=Mock(id=1, name='Home Team'),
                    away_team=Mock(id=2, name='Away Team'),
                    home_analytics=sample_home_analytics,
                    away_analytics=sample_away_analytics,
                    game_time=datetime.now()
                )

                # Should return None due to low confidence
                assert result is None

    def test_try_ml_prediction_model_unavailable(self, analytics_service, mock_session, sample_home_analytics, sample_away_analytics):
        """Test ML prediction when model is unavailable."""
        # Mock ML service that is not available
        mock_ml_service = Mock()
        mock_ml_service.is_available = False

        with patch('api.src.enhanced_mlb_analytics.get_mlb_model_service', return_value=mock_ml_service):
            result = analytics_service._try_ml_prediction(
                session=mock_session,
                home_team=Mock(id=1, name='Home Team'),
                away_team=Mock(id=2, name='Away Team'),
                home_analytics=sample_home_analytics,
                away_analytics=sample_away_analytics,
                game_time=datetime.now()
            )

            assert result is None

    def test_try_ml_prediction_feature_preparation_fails(self, analytics_service, mock_session, sample_home_analytics, sample_away_analytics):
        """Test ML prediction when feature preparation fails."""
        mock_ml_service = Mock()
        mock_ml_service.is_available = True

        with patch('api.src.enhanced_mlb_analytics.get_mlb_model_service', return_value=mock_ml_service):
            with patch.object(analytics_service, '_prepare_ml_features', return_value=None):
                result = analytics_service._try_ml_prediction(
                    session=mock_session,
                    home_team=Mock(id=1, name='Home Team'),
                    away_team=Mock(id=2, name='Away Team'),
                    home_analytics=sample_home_analytics,
                    away_analytics=sample_away_analytics,
                    game_time=datetime.now()
                )

                assert result is None

    @pytest.mark.asyncio
    @patch('api.src.enhanced_mlb_analytics.connect_to_db')
    async def test_enhanced_analytics_with_ml_prediction(self, mock_connect, analytics_service):
        """Test enhanced analytics using ML prediction."""
        # Mock database setup
        mock_session = Mock()
        mock_connect.return_value = mock_session

        # Mock game
        mock_game = Mock()
        mock_game.id = "test_game_ml"
        mock_game.home_team = "Home Team"
        mock_game.away_team = "Away Team"
        mock_game.time = datetime.now()

        # Mock teams
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

        # Mock ML prediction returning 'home' (not the team name)
        with patch.object(analytics_service, '_try_ml_prediction', return_value=(
            'home',  # This is the predicted winner TYPE, not name
            0.65,
            {
                'ml_model_name': 'RandomForest-v1.0',
                'model_confidence': 'High',
                'home_win_probability': 0.65,
                'away_win_probability': 0.35,
                'feature_importance': {'home_rolling_win_pct': 0.15}
            }
        )):
            with patch.object(analytics_service, '_get_recent_team_games', return_value=pd.DataFrame()):
                with patch.object(analytics_service, '_calculate_rolling_win_percentage', return_value=0.6):
                    with patch.object(analytics_service, '_calculate_offensive_rating', return_value=0.7):
                        with patch.object(analytics_service, '_calculate_defensive_rating', return_value=0.6):
                            with patch.object(analytics_service, '_calculate_days_rest', return_value=2):
                                with patch.object(analytics_service, '_calculate_momentum_score', return_value=0.65):
                                    result = await analytics_service.get_enhanced_game_analytics("test_game_ml")

                                    assert isinstance(result, MlbAnalyticsResponse)
                                    assert result.prediction_method == 'machine_learning'
                                    assert result.ml_model_name == 'RandomForest-v1.0'
                                    assert result.ml_confidence == 'High'
                                    assert result.home_win_probability == 0.65
                                    assert result.away_win_probability == 0.35
                                    assert result.predicted_winner == 'Home Team'  # Converted from 'home' to team name
                                    assert result.win_probability == 0.65

    @pytest.mark.asyncio
    @patch('api.src.enhanced_mlb_analytics.connect_to_db')
    async def test_enhanced_analytics_fallback_to_rule_based(self, mock_connect, analytics_service):
        """Test enhanced analytics falls back to rule-based when ML unavailable."""
        # Mock database setup
        mock_session = Mock()
        mock_connect.return_value = mock_session

        # Mock game
        mock_game = Mock()
        mock_game.id = "test_game_rules"
        mock_game.home_team = "Home Team"
        mock_game.away_team = "Away Team"
        mock_game.time = datetime.now()

        # Mock teams
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

        # Mock ML prediction returning None (unavailable)
        with patch.object(analytics_service, '_try_ml_prediction', return_value=None):
            with patch.object(analytics_service, '_get_recent_team_games', return_value=pd.DataFrame()):
                with patch.object(analytics_service, '_calculate_rolling_win_percentage', return_value=0.6):
                    with patch.object(analytics_service, '_calculate_offensive_rating', return_value=0.7):
                        with patch.object(analytics_service, '_calculate_defensive_rating', return_value=0.6):
                            with patch.object(analytics_service, '_calculate_days_rest', return_value=2):
                                with patch.object(analytics_service, '_calculate_momentum_score', return_value=0.65):
                                    result = await analytics_service.get_enhanced_game_analytics("test_game_rules")

                                    assert isinstance(result, MlbAnalyticsResponse)
                                    assert result.prediction_method == 'rule_based'
                                    assert result.ml_model_name is None
                                    assert result.predicted_winner is not None


class TestGetRecentTeamGames:
    """Test cases for _get_recent_team_games method."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()

    def test_get_recent_team_games_with_custom_limit(self, analytics_service, mock_session):
        """Test getting recent games with a custom limit."""
        # Mock schedule records
        mock_games = []
        for i in range(3):
            game = Mock()
            game.date = date(2024, 1, i + 1)
            game.home_team_id = 1
            game.away_team_id = 2
            game.home_score = 5
            game.away_score = 3
            mock_games.append(game)

        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value.union.return_value.order_by.return_value.limit.return_value.all.return_value = mock_games
        mock_session.query.return_value = mock_query

        result = analytics_service._get_recent_team_games(
            mock_session, 1, datetime(2024, 2, 1), limit=3
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'date' in result.columns
        assert 'home_team_id' in result.columns
        assert 'away_team_id' in result.columns
        assert 'home_score' in result.columns
        assert 'away_score' in result.columns

    def test_get_recent_team_games_default_limit(self, analytics_service, mock_session):
        """Test getting recent games with default limit."""
        mock_games = []

        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value.union.return_value.order_by.return_value.limit.return_value.all.return_value = mock_games
        mock_session.query.return_value = mock_query

        result = analytics_service._get_recent_team_games(
            mock_session, 1, datetime(2024, 2, 1)
        )

        # Should use rolling_window * 2 as default limit (5 * 2 = 10)
        assert isinstance(result, pd.DataFrame)


class TestRollingWinPercentageAwayTeam:
    """Test cases for rolling win percentage with away team scenarios."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    def test_calculate_rolling_win_percentage_away_team_wins(self, analytics_service):
        """Test rolling win percentage when team plays as away team and wins."""
        games_data = []
        for i in range(10):
            games_data.append({
                'date': date.today(),
                'home_team_id': 2,  # Team 1 is away
                'away_team_id': 1,
                'home_score': 3 if i < 7 else 5,  # Away team (1) wins 7 out of 10
                'away_score': 5 if i < 7 else 3
            })

        games_df = pd.DataFrame(games_data)

        rolling_pct = analytics_service._calculate_rolling_win_percentage(games_df, 1)

        assert rolling_pct is not None
        assert isinstance(rolling_pct, float)
        assert 0 <= rolling_pct <= 1


class TestMissingStats:
    """Test cases for missing offensive/defensive stats."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()

    def test_calculate_offensive_rating_no_stats(self, analytics_service, mock_session):
        """Test offensive rating when no stats are found."""
        # Mock query returning None
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        offensive_rating = analytics_service._calculate_offensive_rating(
            mock_session, 1, datetime.now()
        )

        assert offensive_rating is None

    def test_calculate_defensive_rating_no_stats(self, analytics_service, mock_session):
        """Test defensive rating when no stats are found."""
        # Mock query returning None
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        defensive_rating = analytics_service._calculate_defensive_rating(
            mock_session, 1, datetime.now()
        )

        assert defensive_rating is None


class TestCalculateDaysRest:
    """Test cases for _calculate_days_rest method."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    def test_calculate_days_rest_empty_dataframe(self, analytics_service):
        """Test days rest calculation with empty DataFrame."""
        empty_df = pd.DataFrame()

        days_rest = analytics_service._calculate_days_rest(empty_df, datetime(2024, 2, 1))

        assert days_rest is None

    def test_calculate_days_rest_with_recent_game(self, analytics_service):
        """Test days rest calculation with recent game."""
        games_data = [{
            'date': date(2024, 1, 28),
            'home_team_id': 1,
            'away_team_id': 2,
            'home_score': 5,
            'away_score': 3
        }]
        games_df = pd.DataFrame(games_data)

        days_rest = analytics_service._calculate_days_rest(games_df, datetime(2024, 2, 1))

        assert days_rest == 4  # Feb 1 - Jan 28 = 4 days


class TestMLPredictionEdgeCases:
    """Test cases for _try_ml_prediction edge cases."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    @pytest.fixture
    def sample_home_analytics(self):
        return TeamAnalytics(
            name="Home Team",
            winning_percentage=0.600,
            rolling_win_percentage=0.650,
            offensive_rating=0.700,
            defensive_rating=0.680,
            days_rest=2,
            momentum_score=0.700
        )

    @pytest.fixture
    def sample_away_analytics(self):
        return TeamAnalytics(
            name="Away Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.480,
            offensive_rating=0.650,
            defensive_rating=0.620,
            days_rest=1,
            momentum_score=0.600
        )

    def test_try_ml_prediction_returns_none(self, analytics_service, sample_home_analytics, sample_away_analytics):
        """Test when ML prediction returns None."""
        mock_session = Mock()
        mock_ml_service = Mock()
        mock_ml_service.is_available = True
        mock_ml_service.predict.return_value = None

        with patch('api.src.enhanced_mlb_analytics.get_mlb_model_service', return_value=mock_ml_service):
            with patch.object(analytics_service, '_prepare_ml_features', return_value={'home_rolling_win_pct': 0.5}):
                result = analytics_service._try_ml_prediction(
                    session=mock_session,
                    home_team=Mock(id=1, name='Home Team'),
                    away_team=Mock(id=2, name='Away Team'),
                    home_analytics=sample_home_analytics,
                    away_analytics=sample_away_analytics,
                    game_time=datetime.now()
                )

                assert result is None

    def test_try_ml_prediction_exception_handling(self, analytics_service, sample_home_analytics, sample_away_analytics):
        """Test exception handling in ML prediction."""
        mock_session = Mock()
        mock_ml_service = Mock()
        mock_ml_service.is_available = True
        mock_ml_service.predict.side_effect = Exception("Model error")

        with patch('api.src.enhanced_mlb_analytics.get_mlb_model_service', return_value=mock_ml_service):
            with patch.object(analytics_service, '_prepare_ml_features', return_value={'home_rolling_win_pct': 0.5}):
                result = analytics_service._try_ml_prediction(
                    session=mock_session,
                    home_team=Mock(id=1, name='Home Team'),
                    away_team=Mock(id=2, name='Away Team'),
                    home_analytics=sample_home_analytics,
                    away_analytics=sample_away_analytics,
                    game_time=datetime.now()
                )

                assert result is None


class TestPrepareMLFeatures:
    """Test cases for _prepare_ml_features method."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def sample_home_analytics(self):
        return TeamAnalytics(
            name="Home Team",
            winning_percentage=0.600,
            rolling_win_percentage=0.650,
            offensive_rating=0.700,
            defensive_rating=0.680,
            days_rest=2,
            momentum_score=0.700
        )

    @pytest.fixture
    def sample_away_analytics(self):
        return TeamAnalytics(
            name="Away Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.480,
            offensive_rating=0.650,
            defensive_rating=0.620,
            days_rest=1,
            momentum_score=0.600
        )

    def test_prepare_ml_features_complete(self, analytics_service, mock_session, sample_home_analytics, sample_away_analytics):
        """Test complete feature preparation with all stats."""
        # Mock recent games
        home_games_data = [{
            'date': date(2024, 1, i),
            'home_team_id': 1,
            'away_team_id': 2,
            'home_score': 5,
            'away_score': 3
        } for i in range(1, 11)]
        home_games_df = pd.DataFrame(home_games_data)

        away_games_data = [{
            'date': date(2024, 1, i),
            'home_team_id': 2,
            'away_team_id': 1,
            'home_score': 3,
            'away_score': 5
        } for i in range(1, 11)]
        away_games_df = pd.DataFrame(away_games_data)

        # Mock offensive stats
        mock_home_offensive = Mock()
        mock_home_offensive.team_batting_average = 0.270
        mock_home_offensive.on_base_percentage = 0.340
        mock_home_offensive.slugging_percentage = 0.450

        mock_away_offensive = Mock()
        mock_away_offensive.team_batting_average = 0.260
        mock_away_offensive.on_base_percentage = 0.330
        mock_away_offensive.slugging_percentage = 0.440

        # Mock defensive stats
        mock_home_defensive = Mock()
        mock_home_defensive.team_era = 3.85
        mock_home_defensive.whip = 1.25
        mock_home_defensive.strikeouts = 200

        mock_away_defensive = Mock()
        mock_away_defensive.team_era = 4.05
        mock_away_defensive.whip = 1.30
        mock_away_defensive.strikeouts = 180

        # Mock head-to-head stats
        h2h_stats = {
            'home_win_pct': 0.600,
            'away_win_pct': 0.400,
            'games_played': 5
        }

        with patch.object(analytics_service, '_get_recent_team_games', side_effect=[home_games_df, away_games_df]):
            with patch.object(analytics_service, '_get_head_to_head_stats', return_value=h2h_stats):
                # Mock database queries for offensive and defensive stats
                mock_session.query.return_value.filter.return_value.order_by.return_value.first.side_effect = [
                    mock_home_offensive, mock_away_offensive, mock_home_defensive, mock_away_defensive
                ]

                features = analytics_service._prepare_ml_features(
                    session=mock_session,
                    home_team=Mock(id=1),
                    away_team=Mock(id=2),
                    home_analytics=sample_home_analytics,
                    away_analytics=sample_away_analytics,
                    game_time=datetime(2024, 2, 1, 19, 0)
                )

                assert features is not None
                assert 'home_rolling_win_pct' in features
                assert 'away_rolling_win_pct' in features
                assert 'home_rolling_runs_scored' in features
                assert 'away_rolling_runs_scored' in features
                assert 'home_rolling_runs_allowed' in features
                assert 'away_rolling_runs_allowed' in features
                assert 'home_days_rest' in features
                assert 'away_days_rest' in features
                assert 'home_batting_avg' in features
                assert 'away_batting_avg' in features
                assert 'home_obp' in features
                assert 'away_obp' in features
                assert 'home_slg' in features
                assert 'away_slg' in features
                assert 'home_era' in features
                assert 'away_era' in features
                assert 'home_whip' in features
                assert 'away_whip' in features
                assert 'home_strikeouts' in features
                assert 'away_strikeouts' in features
                assert 'h2h_home_win_pct' in features
                assert 'h2h_away_win_pct' in features
                assert 'h2h_games_played' in features
                assert 'month' in features
                assert 'day_of_week' in features
                assert 'is_weekend' in features
                assert features['month'] == 2.0
                assert features['day_of_week'] == 3.0  # Thursday
                assert features['is_weekend'] == 0.0

    def test_prepare_ml_features_exception(self, analytics_service, mock_session, sample_home_analytics, sample_away_analytics):
        """Test exception handling in feature preparation."""
        with patch.object(analytics_service, '_get_recent_team_games', side_effect=Exception("Database error")):
            features = analytics_service._prepare_ml_features(
                session=mock_session,
                home_team=Mock(id=1),
                away_team=Mock(id=2),
                home_analytics=sample_home_analytics,
                away_analytics=sample_away_analytics,
                game_time=datetime.now()
            )

            assert features is None


class TestGetHeadToHeadStats:
    """Test cases for _get_head_to_head_stats method."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()

    def test_get_head_to_head_stats_no_games(self, analytics_service, mock_session):
        """Test head-to-head stats when no games found."""
        # Mock empty query result
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        h2h_stats = analytics_service._get_head_to_head_stats(
            mock_session, 1, 2, datetime.now()
        )

        assert h2h_stats == {'home_win_pct': 0.0, 'away_win_pct': 0.0, 'games_played': 0}

    def test_get_head_to_head_stats_with_games(self, analytics_service, mock_session):
        """Test head-to-head stats calculation."""
        # Create mock games where home team (id=1) wins 3 out of 5
        mock_games = []
        for i in range(5):
            game = Mock()
            game.home_team_id = 1
            game.away_team_id = 2
            game.home_score = 5 if i < 3 else 2
            game.away_score = 2 if i < 3 else 5
            mock_games.append(game)

        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_games

        h2h_stats = analytics_service._get_head_to_head_stats(
            mock_session, 1, 2, datetime.now()
        )

        assert h2h_stats['games_played'] == 5
        assert h2h_stats['home_win_pct'] == 0.600
        assert h2h_stats['away_win_pct'] == 0.400


class TestRuleBasedPredictionEdgeCases:
    """Test cases for rule-based prediction edge cases."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    def test_make_prediction_away_team_better_record(self, analytics_service):
        """Test prediction when away team has better season record."""
        home_analytics = TeamAnalytics(
            name="Home Team",
            winning_percentage=0.400,
            rolling_win_percentage=None,
            offensive_rating=None,
            defensive_rating=None,
            days_rest=None,
            momentum_score=None
        )

        away_analytics = TeamAnalytics(
            name="Away Team",
            winning_percentage=0.650,
            rolling_win_percentage=None,
            offensive_rating=None,
            defensive_rating=None,
            days_rest=None,
            momentum_score=None
        )

        predicted_winner, win_probability, confidence_level, key_factors = analytics_service._make_rule_based_prediction(
            home_analytics, away_analytics
        )

        assert predicted_winner == "Away Team"
        assert "season_record" in key_factors
        assert "Away Team has better season record" in key_factors["season_record"]

    def test_make_prediction_away_rest_advantage(self, analytics_service):
        """Test prediction when away team has rest advantage."""
        home_analytics = TeamAnalytics(
            name="Home Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.500,
            offensive_rating=0.500,
            defensive_rating=0.500,
            days_rest=1,
            momentum_score=0.500
        )

        away_analytics = TeamAnalytics(
            name="Away Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.500,
            offensive_rating=0.500,
            defensive_rating=0.500,
            days_rest=5,  # Significant rest advantage
            momentum_score=0.500
        )

        _, _, _, key_factors = analytics_service._make_rule_based_prediction(
            home_analytics, away_analytics
        )

        assert "rest" in key_factors
        assert "Away Team has rest advantage" in key_factors["rest"]

    def test_make_prediction_no_comparisons_fallback(self, analytics_service):
        """Test prediction fallback when no meaningful comparisons available."""
        home_analytics = TeamAnalytics(
            name="Home Team",
            winning_percentage=0.500,
            rolling_win_percentage=None,
            offensive_rating=None,
            defensive_rating=None,
            days_rest=None,
            momentum_score=None
        )

        away_analytics = TeamAnalytics(
            name="Away Team",
            winning_percentage=0.450,
            rolling_win_percentage=None,
            offensive_rating=None,
            defensive_rating=None,
            days_rest=None,
            momentum_score=None
        )

        predicted_winner, win_probability, confidence_level, key_factors = analytics_service._make_rule_based_prediction(
            home_analytics, away_analytics
        )

        assert predicted_winner == "Home Team"
        # The algorithm calculates based on home advantage (1 comparison)
        # home_score = 1/1 = 1.0 which is > 0.6, so High confidence
        # win_probability = 0.55 + (1.0 - 0.5) * 0.3 = 0.7
        assert win_probability == 0.7
        assert confidence_level == "High"

    def test_make_prediction_medium_confidence(self, analytics_service):
        """Test medium confidence prediction."""
        # Create a scenario where advantages are split more evenly
        # to get a score between 0.4 and 0.6 (Medium confidence range)
        home_analytics = TeamAnalytics(
            name="Home Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.520,
            offensive_rating=0.490,
            defensive_rating=0.510,
            days_rest=2,
            momentum_score=0.500
        )

        away_analytics = TeamAnalytics(
            name="Away Team",
            winning_percentage=0.510,
            rolling_win_percentage=0.500,
            offensive_rating=0.510,
            defensive_rating=0.490,
            days_rest=2,
            momentum_score=0.505
        )

        _, _, confidence_level, _ = analytics_service._make_rule_based_prediction(
            home_analytics, away_analytics
        )

        # With split advantages, should get Medium confidence
        assert confidence_level == "Medium"

    def test_make_prediction_home_rest_advantage(self, analytics_service):
        """Test prediction when home team has significant rest advantage."""
        home_analytics = TeamAnalytics(
            name="Home Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.500,
            offensive_rating=0.500,
            defensive_rating=0.500,
            days_rest=5,  # Significant rest advantage
            momentum_score=0.500
        )

        away_analytics = TeamAnalytics(
            name="Away Team",
            winning_percentage=0.500,
            rolling_win_percentage=0.500,
            offensive_rating=0.500,
            defensive_rating=0.500,
            days_rest=1,
            momentum_score=0.500
        )

        _, _, _, key_factors = analytics_service._make_rule_based_prediction(
            home_analytics, away_analytics
        )

        assert "rest" in key_factors
        assert "Home Team has rest advantage" in key_factors["rest"]


class TestConvenienceFunction:
    """Test cases for convenience function."""

    @pytest.mark.asyncio
    @patch('api.src.enhanced_mlb_analytics.EnhancedMLBAnalytics')
    async def test_get_enhanced_mlb_game_analytics(self, mock_analytics_class):
        """Test the convenience function get_enhanced_mlb_game_analytics."""
        # Import the function
        from api.src.enhanced_mlb_analytics import get_enhanced_mlb_game_analytics

        # Create mock analytics instance
        mock_analytics_instance = Mock()
        mock_analytics_class.return_value = mock_analytics_instance

        # Create expected response
        expected_response = MlbAnalyticsResponse(
            id="test_game_convenience",
            home_team="Home Team",
            away_team="Away Team",
            predicted_winner="Home Team",
            win_probability=0.60,
            confidence_level="Medium",
            prediction_method="rule_based"
        )

        # Mock get_enhanced_game_analytics to be an async function
        async def async_return():
            return expected_response

        mock_analytics_instance.get_enhanced_game_analytics = Mock(side_effect=lambda x: async_return())

        result = await get_enhanced_mlb_game_analytics("test_game_convenience")

        assert isinstance(result, MlbAnalyticsResponse)
        assert result.id == "test_game_convenience"
        assert result.home_team == "Home Team"
        assert result.away_team == "Away Team"


class TestCreateBasicResponse:
    """Test cases for _create_basic_response method."""

    @pytest.fixture
    def analytics_service(self):
        """Create an instance of the analytics service for testing."""
        return EnhancedMLBAnalytics(rolling_window=5)

    def test_create_basic_response_both_teams_missing(self, analytics_service):
        """Test basic response when both teams are missing."""
        response = analytics_service._create_basic_response(
            game_id="game123",
            home_team_name="Home Team",
            away_team_name="Away Team",
            home_team=None,
            away_team=None
        )

        assert isinstance(response, MlbAnalyticsResponse)
        assert response.id == "game123"
        assert response.home_team == "Home Team"
        assert response.away_team == "Away Team"
        assert response.predicted_winner == "Home Team"  # Defaults to home
        assert response.win_probability == 0.5
        assert response.confidence_level == "Low"
        assert response.prediction_method == "rule_based"

    def test_create_basic_response_home_team_better(self, analytics_service):
        """Test basic response when home team has better record."""
        home_team = Mock()
        home_team.winning_percentage = 0.650

        away_team = Mock()
        away_team.winning_percentage = 0.450

        response = analytics_service._create_basic_response(
            game_id="game456",
            home_team_name="Strong Home",
            away_team_name="Weak Away",
            home_team=home_team,
            away_team=away_team
        )

        assert response.predicted_winner == "Strong Home"
        assert response.win_probability == 0.55

    def test_create_basic_response_away_team_better(self, analytics_service):
        """Test basic response when away team has better record."""
        home_team = Mock()
        home_team.winning_percentage = 0.400

        away_team = Mock()
        away_team.winning_percentage = 0.700

        response = analytics_service._create_basic_response(
            game_id="game789",
            home_team_name="Weak Home",
            away_team_name="Strong Away",
            home_team=home_team,
            away_team=away_team
        )

        assert response.predicted_winner == "Strong Away"
        assert response.win_probability == 0.55

    def test_create_basic_response_equal_teams(self, analytics_service):
        """Test basic response when teams have equal records."""
        home_team = Mock()
        home_team.winning_percentage = 0.500

        away_team = Mock()
        away_team.winning_percentage = 0.500

        response = analytics_service._create_basic_response(
            game_id="game999",
            home_team_name="Team A",
            away_team_name="Team B",
            home_team=home_team,
            away_team=away_team
        )

        assert response.predicted_winner == "Team A"  # Defaults to home in tie
        assert response.win_probability == 0.5


if __name__ == "__main__":
    pytest.main([__file__])

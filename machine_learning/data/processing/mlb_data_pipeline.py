"""
Data pipeline utilities for MLB data used to make predictions on game outcomes.
"""
from machine_learning.analysis.mlb_feature_engineering import GameFeatureGenerator
from machine_learning.analysis.mlb_time_series import TeamTimeSeriesAnalyzer


class MLBDataPipeline:
    """
    Prepares MLB game data for model training by combining features from multiple sources.
    """
    def __init__(
        self,
        rolling_window: int = 10,
        head_to_head_window: int = 5
    ):
        """
        Initialize the data pipeline.

        Args:
            rolling_window: Number of games to include in rolling calculations
            head_to_head_window: Number of recent matchups to consider for head-to-head features
        """
        self.time_series_analyzer = TeamTimeSeriesAnalyzer(window_size=rolling_window)
        self.feature_generator = GameFeatureGenerator(
            rolling_window=rolling_window,
            head_to_head_window=head_to_head_window
        )
"""
Feature enginering utilities for MLB game predictions.
"""

class GameFeatureGenerator:
    """
    Generates features for a given MLB game using current season data.
    """
    def __init__(
        self,
        rolling_window: int = 10,
        head_to_head_window: int = 5
    ):
        """
        Initialize the feature generator.
        
        Args:
            rolling_window: Number of games to include in rolling calculations
            head_to_head_window: Number of recent matchups to consider for head-to-head features
        """
        self.rolling_window = rolling_window
        self.head_to_head_window = head_to_head_window
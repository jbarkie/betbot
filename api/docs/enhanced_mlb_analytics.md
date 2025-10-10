# Enhanced MLB Analytics

## Overview

The Enhanced MLB Analytics service provides sophisticated game predictions by incorporating machine learning insights and advanced statistical analysis. This represents a significant upgrade from the basic winning percentage comparison to a comprehensive analytical framework.

## Key Features

### 1. Rolling Statistics Analysis

- **Rolling Win Percentage**: Analyzes team performance over the last 10 games to identify momentum trends
- **Recent Form**: Captures whether teams are "hot" or "cold" based on recent performance
- **Momentum Scoring**: Combines multiple metrics to create a momentum score

### 2. Offensive & Defensive Ratings

- **Offensive Rating**: Weighted combination of:
  - Batting Average (30%)
  - On-Base Percentage (40%)
  - Slugging Percentage (30%)
- **Defensive Rating**: Normalized combination of:
  - ERA (60% weight, inverted for positive scale)
  - WHIP (40% weight, inverted for positive scale)

### 3. Rest Advantage Analysis

- **Days of Rest**: Calculates time between games for each team
- **Rest Impact**: Identifies significant rest advantages (2+ days difference)
- **Fatigue Factor**: Considers back-to-back games and extended rest periods

### 4. Enhanced Prediction Logic

- **Multi-Factor Analysis**: Considers season record, momentum, offense, defense, and rest
- **Confidence Levels**: Provides High/Medium/Low confidence based on data availability and factor agreement
- **Key Factors**: Identifies the most important factors influencing the prediction

## API Response Structure

```json
{
  "id": "game_id",
  "home_team": "Home Team Name",
  "away_team": "Away Team Name",
  "predicted_winner": "Predicted Winner",
  "win_probability": 0.65,
  "home_analytics": {
    "name": "Home Team",
    "winning_percentage": 0.6,
    "rolling_win_percentage": 0.7,
    "offensive_rating": 0.75,
    "defensive_rating": 0.68,
    "days_rest": 2,
    "momentum_score": 0.71
  },
  "away_analytics": {
    "name": "Away Team",
    "winning_percentage": 0.5,
    "rolling_win_percentage": 0.4,
    "offensive_rating": 0.65,
    "defensive_rating": 0.72,
    "days_rest": 1,
    "momentum_score": 0.59
  },
  "key_factors": {
    "season_record": "Home Team has better season record",
    "momentum": "Home Team has better recent form",
    "offense": "Home Team has stronger offense",
    "rest": "Home Team has rest advantage (2 vs 1 days)"
  },
  "confidence_level": "High"
}
```

## Implementation Details

### Rolling Window

- Default: 10 games for momentum analysis
- Configurable via `rolling_window` parameter
- Handles insufficient data gracefully

### Data Requirements

- **Required**: Team records (MLBTeam table)
- **Enhanced**: Offensive stats (MLBOffensiveStats table)
- **Enhanced**: Defensive stats (MLBDefensiveStats table)
- **Enhanced**: Game schedule (MLBSchedule table)

### Fallback Behavior

- If enhanced data is unavailable, falls back to basic winning percentage comparison
- Maintains backward compatibility with existing API structure
- Provides "Low" confidence level when using fallback logic

## Usage

The enhanced analytics are automatically used when calling the existing endpoint:

```python
# This now uses enhanced analytics automatically
response = await get_mlb_game_analytics("game_id_123")
```

## Future Enhancements

This implementation provides a solid foundation for further improvements:

1. **Head-to-Head Analysis**: Historical matchup data between specific teams
2. **Temporal Features**: Month/day effects on performance
3. **Weather Integration**: Weather impact on game outcomes
4. **Injury Reports**: Player availability impact
5. **Betting Market Analysis**: Integration with odds movements

## Testing

Comprehensive test suite covers:

- Rolling statistics calculations
- Offensive/defensive rating computations
- Momentum score calculations
- Prediction logic for various scenarios
- Error handling and edge cases

Run tests with:

```bash
pytest api/tests/test_enhanced_mlb_analytics.py
```

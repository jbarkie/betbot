# MLB Prediction Models

This directory stores trained machine learning models for predicting MLB game outcomes.

## Directory Structure

```
mlb/
├── README.md                           # This file
├── mlb_predictor_v2.1.joblib          # Model binary (gitignored)
├── mlb_predictor_v2.1_metadata.json   # Model metadata (tracked in git)
└── .gitkeep                            # Ensures directory is tracked
```

## Training a New Model

To train a new MLB prediction model:

```bash
# From project root with virtual environment activated
python machine_learning/scripts/train_mlb_model.py

# With options
python machine_learning/scripts/train_mlb_model.py \
    --model-type random_forest \
    --version 1.0 \
    --test-split 0.2 \
    --verbose

# Train logistic regression model
python machine_learning/scripts/train_mlb_model.py \
    --model-type logistic_regression \
    --version 1.1
```

### Training Options

- `--model-type`: Type of model (random_forest, logistic_regression, xgboost)
- `--version`: Version string for the model (default: 1.0)
- `--start-date`: Start date for training data (YYYY-MM-DD)
- `--end-date`: End date for training data (YYYY-MM-DD)
- `--test-split`: Fraction for test set (default: 0.2)
- `--verbose`: Enable detailed logging
- `--diagnostics`: Print per-month accuracy, learning curve, class balance, full feature importances
- `--temporal-weighting`: Apply exponential decay weights (recent games weighted higher)
- `--half-life`: Half-life in days for temporal decay (default: 365)
- `--with-pitcher-features`: Include the 6 starting pitcher features (32 total instead of 26); requires `mlb_pitcher_stats` to be populated

### Training Requirements

- At least 100 completed games in the database
- Recent team offensive/defensive statistics
- Rolling game history for each team
- Virtual environment activated with all dependencies installed

## Using a Trained Model

After training a model, update the configuration in `api/src/ml_config.py`:

```python
MLB_MODEL_CONFIG = {
    "model_name": "mlb_predictor",
    "version": "1.0",  # Update this
    "model_file": "mlb_predictor_v1.0.joblib",  # Update this
    "metadata_file": "mlb_predictor_v1.0_metadata.json",  # Update this
    "model_type": "RandomForestClassifier",  # Update this
}
```

Then restart the API server. The model will be lazy-loaded on first prediction request.

## Model Metadata

Each trained model has an accompanying JSON metadata file containing:

- **model_type**: Type of ML algorithm used
- **version**: Model version string
- **trained_date**: ISO timestamp of when model was trained
- **features**: List of all features used
- **metrics**: Performance metrics
  - accuracy, precision, recall, F1 score, ROC AUC
  - Cross-validation scores
  - Training/test set sizes
- **feature_importances**: Importance scores for each feature (tree-based models only)
- **sklearn_version**: Version of scikit-learn used for training

## Model Features (32 total)

### Momentum Features (6)
- `home_rolling_win_pct` - Home team's win % over last 10 games
- `away_rolling_win_pct` - Away team's win % over last 10 games
- `home_rolling_runs_scored` - Avg runs scored (last 10 games)
- `away_rolling_runs_scored` - Avg runs scored (last 10 games)
- `home_rolling_runs_allowed` - Avg runs allowed (last 10 games)
- `away_rolling_runs_allowed` - Avg runs allowed (last 10 games)

### Rest Features (2)
- `home_days_rest` - Days since last game (home team)
- `away_days_rest` - Days since last game (away team)

### Offensive Features (6)
- `home_batting_avg` - Team batting average
- `away_batting_avg` - Team batting average
- `home_obp` - On-base percentage
- `away_obp` - On-base percentage
- `home_slg` - Slugging percentage
- `away_slg` - Slugging percentage

### Defensive Features (6)
- `home_era` - Team ERA (earned run average)
- `away_era` - Team ERA
- `home_whip` - Walks + hits per inning pitched
- `away_whip` - WHIP
- `home_strikeouts` - Team strikeouts (pitching)
- `away_strikeouts` - Team strikeouts (pitching)

### Head-to-Head Features (3)
- `h2h_home_win_pct` - Home team's win % in recent H2H matchups
- `h2h_away_win_pct` - Away team's win % in recent H2H matchups
- `h2h_games_played` - Number of recent H2H games

### Temporal Features (3)
- `month` - Month of game (1-12)
- `day_of_week` - Day of week (0=Monday, 6=Sunday)
- `is_weekend` - Binary flag for weekend games

### Starting Pitcher Features (6, added in v3.3)
Cumulative statistics from the starter's prior starts that season only, sourced
from `mlb_pitcher_stats`. Never includes the game being predicted.
- `home_starter_era` / `away_starter_era` - Starter's ERA entering the game
- `home_starter_whip` / `away_starter_whip` - Starter's WHIP entering the game
- `home_starter_k9` / `away_starter_k9` - Starter's strikeouts per 9 entering the game

Missing values (season debut, or a starter not yet announced) are **median-imputed**
using the medians recorded in the model metadata under `pitcher_medians`. They are
never zero-filled: a 0.00 ERA would present an unknown starter as an untouchable ace.

## Prediction Flow

1. User requests game analytics via `/analytics/mlb/game?id={game_id}`
2. Enhanced analytics service calculates team analytics
3. Service attempts ML prediction:
   - Loads model (if not already cached)
   - Prepares 32 features from database
   - Gets model prediction with probability
   - Checks confidence threshold
4. If ML prediction succeeds with high confidence:
   - Returns ML prediction with probabilities
   - Includes feature importance
   - Sets `prediction_method: "machine_learning"`
5. If ML prediction fails or low confidence:
   - Falls back to rule-based system
   - Sets `prediction_method: "rule_based"`

## Model Version History

| Version | Type | Accuracy | Train Games | Trained | Notes |
|---------|------|----------|-------------|---------|-------|
| v1.0 | RandomForestClassifier | 59.11% | 808 | 2025-10-15 | Late-season data only (low variance) |
| v2.0 | RandomForestClassifier | 53.84% | 4,322 | 2026-04-17 | Full 2024+2025 seasons |
| v2.1 | RandomForestClassifier | 54.57% | 4,243 | 2026-04-21 | Min-games threshold fix |
| v3.0 | RandomForestClassifier | 55.09% | 3,968 (train) | 2026-04-24 | Temporal weighting (365-day half-life); previous production model |
| v3.1 | RandomForestClassifier | 53.87% | 4,550 (train) | 2026-05-20 | Full 2024+2025+2026 dataset (5,688 games); below v3.0 baseline — not promoted; test set skewed toward early-2026 high-variance games |
| v4.0 | XGBClassifier | 50.49% (CV: 56.47%) | 409 (train) | 2026-05-04 | Best params from randomized search (n_iter=50); CV inflated due to small dataset; below RF baseline — not promoted to production |
| v3.2 | RandomForestClassifier | 56.96% | 5,400 (train) | 2026-08-11 | Same config as v3.1, retrained on 6,750 filtered games after the 2026 season matured (744 → 1,789 completed games). Beats v3.0 by 1.87pp; confirms the v3.1 shortfall was a test-split composition artifact, not a data-volume ceiling |
| v3.3 ⭐ | RandomForestClassifier | 56.44% (AUC 0.5708) | 5,400 (train) | 2026-08-11 | Adds 6 starting pitcher features (32 total). Accuracy is 0.52pp below v3.2, well inside the ~1.35pp standard error on a 1,350-game test set, while ROC AUC improves by 0.008. Promoted because the app gates ML vs rule-based at a 0.55 confidence threshold, so ranking quality matters more than thresholded accuracy. Current production model |

## Model Performance Expectations

### RandomForestClassifier
- **Typical Accuracy**: 54-60%
- **Training Time**: 2-5 minutes
- **Prediction Time**: <10ms
- **Pros**: Handles non-linear relationships, provides feature importance
- **Cons**: Larger model file size (~5-20MB)

### LogisticRegression
- **Typical Accuracy**: 52-57%
- **Training Time**: 30-60 seconds
- **Prediction Time**: <5ms
- **Pros**: Fast, interpretable, small model size
- **Cons**: Assumes linear relationships

### XGBoostClassifier
- **Typical Accuracy**: 50-55% (tuned params; see v4.0 findings)
- **Training Time**: 1-3 minutes (+ 5-10 min for `--hyperparameter-search`)
- **Prediction Time**: <5ms
- **Pros**: Built-in missing value handling, strong regularization, supports `--hyperparameter-search`
- **Cons**: Underperforms RF on this dataset at current data volume; re-evaluate when ≥ 2,000 games available

## Model Versioning

Use semantic versioning for models:
- **Major version** (X.0.0): Breaking changes to features or architecture
- **Minor version** (1.X.0): Improved training, new hyperparameters
- **Patch version** (1.0.X): Bug fixes, data updates

## Monitoring Model Performance

Check model info via API:
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/analytics/mlb/model-info
```

Response includes:
- Current model name and version (`ml_model_name`, `ml_model_type`)
- Training date
- Performance metrics
- Load status

## Retraining Schedule

Recommended retraining frequency:
- **During season**: Weekly (as new games complete)
- **Off-season**: Monthly (when roster/stats change)
- **Major updates**: When accuracy drops below 52%

## Troubleshooting

### Model Not Loading
1. Check the file named by `MLB_MODEL_CONFIG['model_file']` exists in `machine_learning/models/mlb/`
2. Verify the matching `metadata_file` sits alongside it in the same directory
3. Check API logs for error messages
4. Ensure scikit-learn version matches training version

### Low Prediction Accuracy
1. Retrain with more recent data
2. Try different model type (RF vs LR)
3. Check for data quality issues
4. Adjust feature engineering

### Predictions Always Use Rule-Based
1. Model file may not exist
2. Confidence threshold too high (check `MIN_CONFIDENCE_THRESHOLD`)
3. Feature preparation failing (check logs)
4. Model loading error (check `get_model_info()` response)

## Git Practices

- ✅ **DO** commit metadata JSON files
- ✅ **DO** commit this README and documentation
- ✅ **DO** document model versions in commit messages
- ❌ **DON'T** commit large .joblib or .pkl files
- ❌ **DON'T** commit models trained on sensitive data
- ❌ **DON'T** force push model binaries

## Future Enhancements

Potential improvements:
- Ensemble models combining multiple algorithms
- XGBoost re-evaluation once ≥ 2,000 games available (Sprint 6 tuning found CV accuracy 56.47% but test accuracy 50.49% — small dataset inflates CV scores)
- Neural networks for complex patterns
- Real-time model retraining pipeline
- A/B testing different model versions
- Starting pitcher features (ERA, WHIP, K/9 for the day's starter)
- Weather and ballpark factors
- Betting market integration

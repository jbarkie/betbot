"""
Visualization utilities for MLB analysis.
"""
from typing import Dict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class TimeSeriesVisualizer:
    """
    Handles visualization of time series analysis results.
    """
    @staticmethod
    def plot_team_momentum(
        rolling_stats: pd.DataFrame,
        team_name: str,
        teams_df: pd.DataFrame
    ) -> None:
        """
        Create visualizations for team momentum analysis.
        
        Args:
            rolling_stats: Rolling statistics calculated for all teams
            team_name: Name of the team to analyze
            teams_df: DataFrame containing team information
        """
        team_id = teams_df[teams_df['name'] == team_name]['id'].iloc[0]
        team_rolling = rolling_stats[rolling_stats['team_id'] == team_id].copy()
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        
        # Win percentage plot
        ax1.plot(team_rolling['date'], team_rolling['rolling_win_pct'])
        ax1.set_title(f'{team_name} Rolling Win Percentage')
        ax1.set_ylabel('Win %')
        ax1.grid(True)
        
        # Runs plot
        ax2.plot(team_rolling['date'], team_rolling['rolling_runs_scored'],
                label='Runs Scored')
        ax2.plot(team_rolling['date'], team_rolling['rolling_runs_allowed'],
                label='Runs Allowed')
        ax2.set_title(f'{team_name} Rolling Run Production/Prevention')
        ax2.set_ylabel('Runs per Game')
        ax2.legend()
        ax2.grid(True)
        
        # Streak plot
        ax3.plot(team_rolling['date'], team_rolling['streak'])
        ax3.set_title(f'{team_name} Rolling Win Streak')
        ax3.set_ylabel('Wins in Last 10 Games')
        ax3.grid(True)
        
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_rest_impact(rest_impact: Dict[str, float]) -> None:
        """
        Create visualization for rest day impact analysis.
        
        Args:
            rest_impact: Dictionary containing win percentages by rest category
        """
        plt.figure(figsize=(10, 6))
        pd.Series(rest_impact).plot(kind='bar')
        plt.title('Impact of Rest Days on Win Percentage')
        plt.xlabel('Days of Rest')
        plt.ylabel('Average Win Percentage')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_team_performance_comparison(
        hot_teams: pd.DataFrame,
        cold_teams: pd.DataFrame,
        metrics: list = ['rolling_win_pct', 'rolling_runs_scored', 'rolling_runs_allowed']
    ) -> None:
        """
        Create a visual comparison of hot and cold teams' performance metrics.
        
        Args:
            hot_teams: DataFrame containing statistics for hot teams
            cold_teams: DataFrame containing statistics for cold teams
            metrics: List of metrics to compare
        """
        # Set the style using seaborn's default style
        sns.set_style("whitegrid")
        
        # Create subplots for each metric
        fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 4*len(metrics)))
        if len(metrics) == 1:
            axes = [axes]
            
        for idx, metric in enumerate(metrics):
            # Prepare data for plotting
            hot_data = hot_teams[['name', metric]].copy()
            cold_data = cold_teams[['name', metric]].copy()
            hot_data['status'] = 'Hot'
            cold_data['status'] = 'Cold'
            plot_data = pd.concat([hot_data, cold_data])
            
            # Create the bar plot
            sns.barplot(
                data=plot_data,
                x='name',
                y=metric,
                hue='status',
                palette={'Hot': 'red', 'Cold': 'blue'},
                ax=axes[idx]
            )
            
            # Customize the plot
            axes[idx].set_title(f'Team Comparison - {metric.replace("_", " ").title()}')
            axes[idx].set_xlabel('Team')
            axes[idx].set_ylabel(metric.replace('_', ' ').title())
            axes[idx].tick_params(axis='x', rotation=45)
            
            # Add value labels on the bars
            for p in axes[idx].patches:
                axes[idx].annotate(
                    f'{p.get_height():.3f}',
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center',
                    va='bottom'
                )
        
        plt.tight_layout()
        plt.show()
        
        # Print summary statistics
        print("\nHot Teams Summary:")
        print(hot_teams[['name', 'rolling_win_pct', 'rolling_runs_scored', 'rolling_runs_allowed']]
              .to_string(index=False, float_format=lambda x: f'{x:.3f}'))
        
        print("\nCold Teams Summary:")
        print(cold_teams[['name', 'rolling_win_pct', 'rolling_runs_scored', 'rolling_runs_allowed']]
              .to_string(index=False, float_format=lambda x: f'{x:.3f}'))
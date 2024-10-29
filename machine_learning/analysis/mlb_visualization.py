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
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Win percentage plot with league average
        league_avg_win_pct = rolling_stats['rolling_win_pct'].mean()
        ax1.plot(team_rolling['date'], team_rolling['rolling_win_pct'], 
                label='Team Win %', linewidth=2)
        ax1.axhline(y=league_avg_win_pct, color='r', linestyle='--', 
                   label='League Average', alpha=0.5)
        ax1.set_title(f'{team_name} Rolling Win Percentage')
        ax1.set_ylabel('Win %')
        ax1.grid(True)
        ax1.legend()
        
        # Runs for/against plots with run differential
        ax2.plot(team_rolling['date'], team_rolling['rolling_runs_scored'],
                label='Runs Scored', color='green', linewidth=2)
        ax2.plot(team_rolling['date'], team_rolling['rolling_runs_allowed'],
                label='Runs Allowed', color='red', linewidth=2)
        team_rolling['run_differential'] = (
            team_rolling['rolling_runs_scored'] - team_rolling['rolling_runs_allowed']
        )
        ax2_twin = ax2.twinx()
        ax2_twin.plot(team_rolling['date'], team_rolling['run_differential'],
                     label='Run Differential', color='blue', linestyle='--', alpha=0.5)
        
        # Set titles and labels
        ax2.set_title(f'{team_name} Run Production and Prevention')
        ax2.set_ylabel('Runs per Game', color='black')
        ax2_twin.set_ylabel('Run Differential', color='blue')
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2_twin.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # Add summary statistics
        latest_stats = team_rolling.iloc[-1]
        summary_text = (
            f"Latest Statistics:\n"
            f"Win %: {latest_stats['rolling_win_pct']:.3f}\n"
            f"Runs Scored/Game: {latest_stats['rolling_runs_scored']:.2f}\n"
            f"Runs Allowed/Game: {latest_stats['rolling_runs_allowed']:.2f}\n"
            f"Run Differential/Game: {latest_stats['run_differential']:.2f}\n"
            f"Days Since Last Game: {latest_stats['days_rest']:.0f}"
        )
        
        plt.figtext(0.02, 0.02, summary_text, fontsize=10, 
                   bbox=dict(facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.show()
        
        # Print additional insights
        print(f"\nTeam Performance Insights for {team_name}:")
        print(f"- {'Above' if latest_stats['rolling_win_pct'] > league_avg_win_pct else 'Below'} "
              f"league average win percentage "
              f"({latest_stats['rolling_win_pct']:.3f} vs {league_avg_win_pct:.3f})")
        
        run_diff_trend = team_rolling['run_differential'].iloc[-5:].mean()
        print(f"- Recent run differential trend (last 5 games): {run_diff_trend:+.2f} runs/game")
        
        if abs(latest_stats['days_rest']) > 2:
            print(f"- Extended rest period: {latest_stats['days_rest']:.0f} days since last game")

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
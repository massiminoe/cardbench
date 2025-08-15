#!/usr/bin/env python3

import argparse
import csv
import os
import sys

from tournament_stats import TournamentAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Analyze tournament results and calculate ELO ratings")
    parser.add_argument("tournament_dir", help="Path to tournament results directory")
    parser.add_argument("--bootstrap-samples", type=int, default=1000, 
                       help="Number of bootstrap samples for confidence intervals (default: 1000)")
    parser.add_argument("--export-csv", type=str, 
                       help="Export results to CSV file (e.g., results.csv)")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.tournament_dir):
        print(f"Error: Directory {args.tournament_dir} does not exist")
        sys.exit(1)
    
    print(f"Analyzing tournament: {os.path.basename(args.tournament_dir)}")
    print(f"Loading games from: {args.tournament_dir}")
    
    analyzer = TournamentAnalyzer(args.tournament_dir)
    agent_stats = analyzer.analyze(bootstrap_samples=args.bootstrap_samples)
    
    total_games = len(analyzer.games)
    num_agents = len(analyzer.agents)
    
    print(f"\nTournament Analysis: {os.path.basename(args.tournament_dir)} ({total_games} games, {num_agents} agents)")
    print("=" * 80)
    
    print("\nFinal ELO Rankings:")
    print(f"{'Rank':<4} {'Agent':<30} {'ELO':<6} {'90% CI':<12} {'Games':<6} {'W-L-D':<8} {'Win%':<6} {'Err%':<6}")
    print("-" * 85)
    
    for i, stats in enumerate(agent_stats, 1):
        ci_str = f"[{stats.elo_ci_low:.0f}-{stats.elo_ci_high:.0f}]"
        wld_str = f"{stats.wins}-{stats.losses}-{stats.draws}"
        
        print(f"{i:<4} {stats.name:<30} {stats.elo_rating:<6.0f} {ci_str:<12} "
              f"{stats.games_played:<6} {wld_str:<8} {stats.win_percentage:<6.1f}% {stats.error_loss_percentage:<6.1f}%")
    
    # Export to CSV if requested
    if args.export_csv:
        print(f"\nExporting results to {args.export_csv}")
        with open(args.export_csv, 'w', newline='') as csvfile:
            fieldnames = ['Rank', 'Agent', 'ELO', 'CI_Low', 'CI_High', 'Games', 'Wins', 'Losses', 'Draws', 'Win_Percentage', 'Error_Percentage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for i, stats in enumerate(agent_stats, 1):
                writer.writerow({
                    'Rank': i,
                    'Agent': stats.name,
                    'ELO': round(stats.elo_rating, 0),
                    'CI_Low': round(stats.elo_ci_low, 0),
                    'CI_High': round(stats.elo_ci_high, 0),
                    'Games': stats.games_played,
                    'Wins': stats.wins,
                    'Losses': stats.losses,
                    'Draws': stats.draws,
                    'Win_Percentage': round(stats.win_percentage, 1),
                    'Error_Percentage': round(stats.error_loss_percentage, 1)
                })
        print(f"CSV export completed!")


if __name__ == "__main__":
    main()
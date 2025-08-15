import json
import os
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Tuple

from elo_rating import EloRating


@dataclass
class GameResult:
    agent_0_name: str
    agent_1_name: str
    agent_0_score: float
    agent_1_score: float
    event_log: List[str]
    details: str


@dataclass
class AgentStats:
    name: str
    elo_rating: float
    elo_ci_low: float
    elo_ci_high: float
    games_played: int
    wins: int
    losses: int
    draws: int
    win_percentage: float
    error_losses: int
    error_loss_percentage: float  # % of games where agent errored out


class TournamentAnalyzer:
    def __init__(self, tournament_dir: str):
        self.tournament_dir = tournament_dir
        self.games: List[GameResult] = []
        self.agents: set = set()
        
    def load_games(self):
        json_files = [f for f in os.listdir(self.tournament_dir) if f.endswith('.json')]
        json_files.sort()  # Sort by filename (timestamp order)
        
        for filename in json_files:
            filepath = os.path.join(self.tournament_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    game = GameResult(**data)
                    self.games.append(game)
                    self.agents.add(game.agent_0_name)
                    self.agents.add(game.agent_1_name)
            except Exception as e:
                print(f"Warning: Skipping malformed file {filename}: {e}")
    
    def calculate_basic_stats(self) -> Dict[str, Dict]:
        stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'error_losses': 0})
        
        for game in self.games:
            stats[game.agent_0_name]['games'] += 1
            stats[game.agent_1_name]['games'] += 1
            
            # Check for error-based losses
            error_match = re.search(r"Agent (\d+) reached max error count", game.details)
            error_agent_pos = None
            if error_match:
                error_agent_pos = int(error_match.group(1))
            
            if game.agent_0_score > game.agent_1_score:
                stats[game.agent_0_name]['wins'] += 1
                stats[game.agent_1_name]['losses'] += 1
                # Agent 1 lost - check if due to errors
                if error_agent_pos == 1:
                    stats[game.agent_1_name]['error_losses'] += 1
            elif game.agent_1_score > game.agent_0_score:
                stats[game.agent_1_name]['wins'] += 1
                stats[game.agent_0_name]['losses'] += 1
                # Agent 0 lost - check if due to errors
                if error_agent_pos == 0:
                    stats[game.agent_0_name]['error_losses'] += 1
            else:
                stats[game.agent_0_name]['draws'] += 1
                stats[game.agent_1_name]['draws'] += 1
        
        return dict(stats)
    
    def calculate_elo_ratings(self) -> Dict[str, float]:
        elo = EloRating()
        
        for game in self.games:
            elo.update_ratings(game.agent_0_name, game.agent_1_name, game.agent_0_score)
        
        return elo.get_all_ratings()
    
    def bootstrap_elo_confidence(self, bootstrap_samples: int = 1000) -> Dict[str, Tuple[float, float]]:
        confidence_intervals = {}
        
        for agent in self.agents:
            bootstrap_ratings = []
            
            for _ in range(bootstrap_samples):
                # Resample games with replacement
                resampled_games = random.choices(self.games, k=len(self.games))
                
                # Calculate ELO for this bootstrap sample
                elo = EloRating()
                for game in resampled_games:
                    elo.update_ratings(game.agent_0_name, game.agent_1_name, game.agent_0_score)
                
                bootstrap_ratings.append(elo.get_rating(agent))
            
            # Calculate 90% confidence interval (5th and 95th percentiles)
            bootstrap_ratings.sort()
            ci_low = bootstrap_ratings[int(0.05 * len(bootstrap_ratings))]
            ci_high = bootstrap_ratings[int(0.95 * len(bootstrap_ratings))]
            confidence_intervals[agent] = (ci_low, ci_high)
        
        return confidence_intervals
    
    def analyze(self, bootstrap_samples: int = 1000) -> List[AgentStats]:
        self.load_games()
        
        basic_stats = self.calculate_basic_stats()
        elo_ratings = self.calculate_elo_ratings()
        elo_confidence = self.bootstrap_elo_confidence(bootstrap_samples)
        
        agent_stats = []
        for agent in self.agents:
            stats = basic_stats[agent]
            elo = elo_ratings.get(agent, 1500)
            ci_low, ci_high = elo_confidence[agent]
            
            win_pct = stats['wins'] / stats['games'] * 100 if stats['games'] > 0 else 0
            error_game_pct = stats['error_losses'] / stats['games'] * 100 if stats['games'] > 0 else 0
            
            agent_stats.append(AgentStats(
                name=agent,
                elo_rating=elo,
                elo_ci_low=ci_low,
                elo_ci_high=ci_high,
                games_played=stats['games'],
                wins=stats['wins'],
                losses=stats['losses'],
                draws=stats['draws'],
                win_percentage=win_pct,
                error_losses=stats['error_losses'],
                error_loss_percentage=error_game_pct
            ))
        
        # Sort by ELO rating (descending)
        agent_stats.sort(key=lambda x: x.elo_rating, reverse=True)
        return agent_stats
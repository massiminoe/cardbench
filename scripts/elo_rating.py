import math
from typing import Dict


class EloRating:
    def __init__(self, starting_rating: int = 1500, k_factor: int = 32):
        self.starting_rating = starting_rating
        self.k_factor = k_factor
        self.ratings: Dict[str, float] = {}
    
    def get_rating(self, agent: str) -> float:
        return self.ratings.get(agent, self.starting_rating)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))
    
    def update_ratings(self, agent_a: str, agent_b: str, score_a: float):
        rating_a = self.get_rating(agent_a)
        rating_b = self.get_rating(agent_b)
        
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = 1.0 - expected_a
        
        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * ((1.0 - score_a) - expected_b)
        
        self.ratings[agent_a] = new_rating_a
        self.ratings[agent_b] = new_rating_b
    
    def get_all_ratings(self) -> Dict[str, float]:
        return self.ratings.copy()
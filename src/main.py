from src.games.go_fish.go_fish import GoFish
from src.agents.random import RandomAgent
from src.controller import run_discrete_game


if __name__ == "__main__":
    game_cls = GoFish
    agents = [RandomAgent(0), RandomAgent(1)]
    result = run_discrete_game(game_cls, agents, log_events=True)
    print(result)
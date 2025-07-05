import logging

from src.games.go_fish.go_fish import GoFish
from src.agents.random import RandomAgent
from src.agents.llm.llm import LLMAgent
from src.controller import run_discrete_game

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

if __name__ == "__main__":
    game_cls = GoFish
    agents = [RandomAgent, LLMAgent]
    result = run_discrete_game(game_cls, agents, log_events=True)
    print(result)

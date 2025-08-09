import logging

from src.games.gin_rummy.gin_rummy import GinRummy
from src.games.crazy_eights.crazy_eights import CrazyEights
from src.games.go_fish.go_fish import GoFish
from src.agents.random import RandomAgent
from src.agents.llm.llm import LLMAgent
from src.controller import run_discrete_game

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

if __name__ == "__main__":
    # Forcefully configure logging with timestamp and clean format
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    # game_cls = GoFish
    game_cls = GinRummy
    agents = [RandomAgent, LLMAgent]
    # agents = [RandomAgent, RandomAgent]
    result = run_discrete_game(game_cls, agents, log_events=True)
    print(result)

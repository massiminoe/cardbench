import logging

from src.games.gin_rummy.gin_rummy import GinRummy
from src.games.crazy_eights.crazy_eights import CrazyEights
from src.games.go_fish.go_fish import GoFish
from src.agents.random import RandomAgent
from src.agents.llm.llm import LLMAgent
from src.controller import run_and_save_discrete_game

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
    agent_0_cls = RandomAgent
    agent_1_cls = LLMAgent
    result = run_and_save_discrete_game(game_cls, agent_0_cls, agent_1_cls, log_events=True)
    print(result)

"""
Interface to run a tournament of games.
"""

import datetime as dt
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from src.agents.common import DiscreteAgent
from src.agents.random import RandomAgent
from src.agents.llm.llm import LLMAgent
from src.games.common import DiscreteGame
from src.games.go_fish.go_fish import GoFish
from src.games.gin_rummy.gin_rummy import GinRummy
from src.games.crazy_eights.crazy_eights import CrazyEights
from src.controller import run_and_save_discrete_game

logger = logging.getLogger(__name__)

MODEL_IDS = [
    "google/gemma-3-27b-it",
    "google/gemini-2.5-flash-lite",
    "x-ai/grok-3-mini",
    "openai/gpt-5-nano",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-4.1-nano",
    "openai/gpt-4o-mini",
    "openai/gpt-5-mini",
    "openai/gpt-4.1-mini",
    "anthropic/claude-3.5-haiku-20241022",
]
# agent_cls, agent_kwargs
AGENTS: list[tuple[type[DiscreteAgent], dict]] = [(RandomAgent, {})] + [
    (LLMAgent, {"model_id": model_id}) for model_id in MODEL_IDS
]


def run_tournament(
    agents: list[tuple[type[DiscreteAgent], dict]],
    game: type[DiscreteGame],
    n_total_games: int,
    tournament_id: str | None = None,
    max_workers: int = 20,
) -> None:
    """
    Run a tournament of games.
    """
    if tournament_id is None:
        tournament_id = f"{game.__name__}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Running tournament {tournament_id} with {n_total_games} games...")

    # Generate pairs of agents in round-robin format until we have enough games
    agent_pairs = []
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            agent_pairs.append((agents[i], agents[j]))
    agent_pairs *= (n_total_games // len(agent_pairs)) + 1
    agent_pairs = agent_pairs[:n_total_games]

    # Run all the games in parallel
    results_dir = f"./results/{tournament_id}"
    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for (agent_0_cls, agent_0_kwargs), (agent_1_cls, agent_1_kwargs) in agent_pairs:
            futures.append(
                executor.submit(
                    run_and_save_discrete_game,
                    game,
                    agent_0_cls,
                    agent_1_cls,
                    agent_0_kwargs,
                    agent_1_kwargs,
                    False,
                    results_dir,
                )
            )

        with tqdm(total=len(futures), desc="Games", unit="game") as pbar:
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    logger.exception("A game failed during tournament execution")
                finally:
                    pbar.update(1)


if __name__ == "__main__":
    run_tournament(
        agents=AGENTS,
        game=GinRummy,
        n_total_games=200,
        tournament_id="gin_rummy_v1",
        max_workers=10,
    )

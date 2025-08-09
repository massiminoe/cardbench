import random

import pytest

from src.controller import run_discrete_game
from src.games.go_fish.go_fish import GoFish
from src.games.crazy_eights.crazy_eights import CrazyEights
from src.games.gin_rummy.gin_rummy import GinRummy
from src.agents.random import RandomAgent
from src.games.common import GameResult


@pytest.fixture(autouse=True)
def fixed_seed():
    random.seed(2024)


@pytest.mark.parametrize(
    "game_cls",
    [GoFish, CrazyEights, GinRummy],
)
def test_run_game_random_agents(game_cls):
    """Ensure a full game can be played between two RandomAgents without error."""
    result = run_discrete_game(game_cls, RandomAgent, RandomAgent)
    assert isinstance(result, GameResult)
    assert isinstance(result.agent_0_name, str)
    assert isinstance(result.agent_1_name, str)
    assert isinstance(result.agent_0_score, (int, float))
    assert isinstance(result.agent_1_score, (int, float))
    assert isinstance(result.event_log, list)
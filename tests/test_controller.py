import random

import pytest

from src.controller import run_discrete_game
from src.games.go_fish.go_fish import GoFish
from src.games.crazy_eights.crazy_eights import CrazyEights
from src.agents.random import RandomAgent
from src.games.common import BinaryGameResult


@pytest.fixture(autouse=True)
def fixed_seed():
    random.seed(2024)


@pytest.mark.parametrize(
    "game_cls",
    [GoFish, CrazyEights],
)
def test_run_game_random_agents(game_cls):
    """Ensure a full game can be played between two RandomAgents without error."""
    result = run_discrete_game(game_cls, [RandomAgent, RandomAgent])
    assert isinstance(result, BinaryGameResult)
    # One of the outcome indicators must be set.
    assert result.draw or (result.winner is not None and result.loser is not None) 
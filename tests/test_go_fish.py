import random
from collections import Counter

import pytest

from src.games.go_fish.go_fish import GoFish, Action
from src.games.common import Card, BinaryGameResult, RANKS


@pytest.fixture(autouse=True)
def fixed_seed():
    random.seed(1234)


def _setup_game():
    game = GoFish(agent_ids=[0, 1])
    game.init_game()
    return game


def test_actions_are_valid():
    game = _setup_game()
    agent = game.current_agent
    for action in game.get_agent_actions(agent):
        assert game.validate_action(agent, action)


def test_successful_steal_and_book():
    game = _setup_game()

    # Force a predictable state: agent 0 can steal and make a book
    game.current_agent = 0
    game.hands = {
        0: [Card("7", "C"), Card("7", "D"), Card("7", "H")],
        1: [Card("7", "S"), Card("9", "C")],
    }
    game.books = {0: [], 1: []}
    game.stock = []
    game.total_books = 0

    action = Action(rank="7", target_agent_id=1)
    game.step(action)

    # Agent 0 should have created a book of 7s
    assert "7" in game.books[0]
    assert len(game.books[0]) == 1
    # All 7s removed from hand
    ranks_after = Counter(card.rank for card in game.hands[0])
    assert ranks_after["7"] == 0
    # Total books updated
    assert game.total_books == 1


def test_draw_when_rank_absent():
    game = _setup_game()
    game.current_agent = 0

    # Configure hands so target lacks the requested rank
    game.hands = {
        0: [Card("5", "C")],
        1: [Card("9", "D")],
    }
    game.books = {0: [], 1: []}
    game.stock = [Card("8", "C"), Card("K", "H")]

    action = Action(rank="5", target_agent_id=1)
    hand_size_before = len(game.hands[0])
    next_agent = game.step(action)

    # Agent 0 should have drawn a card
    assert len(game.hands[0]) == hand_size_before + 1
    # Turn passes to agent 1
    assert next_agent == 1


def test_game_completion_and_result():
    game = _setup_game()
    game.current_agent = 0

    # Pre-set 12 books for agent 0, none for agent 1
    twelve_ranks = [r for r in RANKS if r != "9"]
    game.books = {0: twelve_ranks, 1: []}
    game.total_books = 12

    game.hands = {
        0: [Card("9", "C"), Card("9", "D"), Card("9", "H")],
        1: [Card("9", "S")],
    }
    game.stock = []

    action = Action(rank="9", target_agent_id=1)
    game.step(action)  # This should create the 13th book and end the game

    assert game.done
    result = game.get_game_result()
    assert isinstance(result, BinaryGameResult)
    assert result.winner == 0
    assert result.loser == 1 
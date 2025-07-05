import random

import pytest

from src.games.crazy_eights.crazy_eights import CrazyEights, Action
from src.games.common import Card, BinaryGameResult


@pytest.fixture(autouse=True)
def fixed_seed():
    """Ensure deterministic shuffling for reproducible tests."""
    random.seed(42)


def _setup_game():
    game = CrazyEights(agent_ids=[0, 1])
    game.init_game()
    return game


def test_actions_are_valid():
    """Every action returned by get_agent_actions should validate."""
    game = _setup_game()
    agent_id = game.current_agent
    actions = game.get_agent_actions(agent_id)
    # There should be at least one legal action each turn
    assert len(actions) > 0
    for action in actions:
        assert game.validate_action(agent_id, action), f"Action {action} should be valid"


def test_single_turn_progression():
    """After a valid action, the turn should advance to the next agent (unless game ends)."""
    game = _setup_game()
    current = game.current_agent
    actions = game.get_agent_actions(current)
    chosen = actions[0]
    next_agent = game.step(chosen)
    if next_agent is not None:
        assert next_agent == (current + 1) % game.num_agents
        assert game.current_agent == next_agent


def test_play_eight_changes_suit():
    """Playing an eight should allow the player to declare a new suit."""
    game = _setup_game()
    agent = game.current_agent

    # Give the current agent a guaranteed eight to play
    eight_card = Card("8", "C")
    game.hands[agent].append(eight_card)
    declared_suit = "H"
    action = Action(play_card=eight_card, declare_suit=declared_suit)
    assert game.validate_action(agent, action)
    game.step(action)

    assert game.current_suit == declared_suit
    assert game.current_rank == "8"


def test_stalemate_winner_by_fewest_cards():
    """When in stalemate, the player with the fewest cards should win."""
    game = _setup_game()

    # Force a stalemate scenario
    game.stock = []  # No cards to draw
    game.current_suit = "H"
    game.current_rank = "K"

    # Configure hands so agent 0 has 1 card, agent 1 has 2 cards, none playable
    game.hands = {
        0: [Card("2", "C")],
        1: [Card("3", "D"), Card("4", "S")],
    }

    # Ensure no card is an eight or matches suit/rank
    assert all(card.rank != "8" and card.suit != game.current_suit and card.rank != game.current_rank for hand in game.hands.values() for card in hand)

    # It is agent 0's turn. They must pass.
    game.current_agent = 0
    action_pass = Action(is_pass=True)

    # Agent 0 passes; stalemate should be detected immediately
    game.step(action_pass)

    assert game.done
    result = game.get_game_result()
    assert isinstance(result, BinaryGameResult)
    assert result.winner == 0
    assert result.loser == 1


def test_stalemate_draw_when_equal_cards():
    game = _setup_game()
    game.stock = []
    game.current_suit = "H"
    game.current_rank = "K"

    game.hands = {
        0: [Card("2", "C")],
        1: [Card("3", "D")],
    }

    game.current_agent = 0
    action_pass = Action(is_pass=True)
    game.step(action_pass)

    assert game.done
    result = game.get_game_result()
    assert result.draw is True 
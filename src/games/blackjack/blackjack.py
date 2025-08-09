from dataclasses import dataclass
from enum import Enum, auto
import random
import logging

from src.games.common import Card, Deck, DiscreteGame, BinaryGameResult, SUITS, RANKS


class ActionType(Enum):
    HIT = auto()
    STAND = auto()


@dataclass
class Action:
    action_type: ActionType

    def __str__(self):
        return self.action_type.name

    def __eq__(self, other):
        if not isinstance(other, Action):
            return NotImplemented
        return self.action_type == other.action_type



class Blackjack(DiscreteGame):
    """
    Implements a single-player game of Blackjack against a dealer.
    The agent is always agent_id 0.
    """

    def __init__(self, agent_ids: list[int] = [0], log_events: bool = False):
        if len(agent_ids) != 1:
            raise ValueError("Blackjack is a single-player game against the dealer.")
        super().__init__(agent_ids=agent_ids, game_name="blackjack", log_events=log_events)

    def init_game(self):
        """Initializes a new game of Blackjack."""
        self.deck = Deck()
        self.player_hand: list[Card] = self.deck.deal_with_replacement(2)
        self.dealer_hand: list[Card] = self.deck.deal_with_replacement(1)

        self.done = False
        self.payout = 0.0

        # Player's turn unless they have Blackjack
        self.phase = "player_turn"
        self.event_log.push(f"Player hand: {self.player_hand}, Dealer shows: {self.dealer_hand[0]}")

        # If player has blackjack, their turn is skipped
        if self._get_hand_value(self.player_hand) == 21:
            self.event_log.push("Player has Blackjack!")
            self._play_dealer_turn()

    def _get_card_value(self, card: Card) -> int:
        """Returns the integer value of a card."""
        if card.rank.isdigit():
            return int(card.rank)
        if card.rank in ["T", "J", "Q", "K"]:
            return 10
        if card.rank == "A":
            return 11  # Initially treat Ace as 11
        return 0

    def _get_hand_value(self, hand: list[Card]) -> int:
        """Calculates the value of a hand, handling Aces optimally."""
        value = sum(self._get_card_value(card) for card in hand)
        num_aces = sum(1 for card in hand if card.rank == "A")

        # Reduce value for each Ace if hand is over 21
        while value > 21 and num_aces > 0:
            value -= 10
            num_aces -= 1
        return value

    def step(self, action: Action | None) -> int | None:
        """Processes a single player action (HIT or STAND)."""
        assert not self.done, "Game is already finished."
        assert action is not None, "Action required"
        assert self.phase == "player_turn", "Not player's turn"

        self.event_log.push(f"[Agent {self.current_agent}] {action}")

        if action.action_type == ActionType.HIT:
            new_card = self.deck.deal_with_replacement(1)[0]
            self.player_hand.append(new_card)
            self.event_log.push(f"Player hits, gets {new_card}. Hand: {self.player_hand}")
            player_value = self._get_hand_value(self.player_hand)
            if player_value > 21:
                self.event_log.push(f"Player busts with {player_value}.")
                self.payout = -1.0
                self.done = True

        elif action.action_type == ActionType.STAND:
            player_value = self._get_hand_value(self.player_hand)
            self.event_log.push(f"Player stands with {player_value}.")
            self._play_dealer_turn()

        return None if self.done else self.current_agent

    def _play_dealer_turn(self):
        """Plays the dealer's hand according to fixed rules."""
        self.phase = "dealer_turn"
        
        # Dealer draws a second card
        dealer_hand_value = self._get_hand_value(self.dealer_hand)
        self.event_log.push(f"Dealer's turn. Hand: {self.dealer_hand} ({dealer_hand_value})")

        while self._get_hand_value(self.dealer_hand) < 17:
            new_card = self.deck.deal_with_replacement(1)[0]
            self.dealer_hand.append(new_card)
            dealer_hand_value = self._get_hand_value(self.dealer_hand)
            self.event_log.push(f"Dealer hits, gets {new_card}. Hand: {self.dealer_hand} ({dealer_hand_value})")

        dealer_value = self._get_hand_value(self.dealer_hand)
        if dealer_value > 21:
            self.event_log.push(f"Dealer busts with {dealer_value}.")

        self._resolve_game()

    def _resolve_game(self):
        """Determines the winner and sets the payout."""
        player_value = self._get_hand_value(self.player_hand)
        dealer_value = self._get_hand_value(self.dealer_hand)
        
        player_has_blackjack = player_value == 21 and len(self.player_hand) == 2
        dealer_has_blackjack = dealer_value == 21 and len(self.dealer_hand) == 2

        self.event_log.push(f"Game resolved: Player ({player_value}), Dealer ({dealer_value})")

        if player_value > 21: # Player bust case handled in step()
            self.payout = -1.0
        elif dealer_value > 21:
            self.payout = 1.0
        elif player_has_blackjack and not dealer_has_blackjack:
            self.payout = 1.5
        elif not player_has_blackjack and dealer_has_blackjack:
            self.payout = -1.0
        elif player_value > dealer_value:
            self.payout = 1.0
        elif player_value < dealer_value:
            self.payout = -1.0
        else: # Push
            self.payout = 0.0

        self.done = True
        self.event_log.push(f"Payout: {self.payout}")

    def get_agent_actions(self, agent_id: int) -> list[Action]:
        """Returns the legal actions for the player."""
        if self.done or self.phase != "player_turn":
            return []
        return [Action(ActionType.HIT), Action(ActionType.STAND)]

    def get_agent_state(self, agent_id: int) -> dict:
        """Returns the agent's view of the game state."""
        return {
            "player_hand": self.player_hand,
            "dealer_hand": self.dealer_hand,  # Full hand visible in state
            "payout": self.payout if self.done else None,
        }

    def get_payout(self) -> float:
        """Returns the final payout of the game."""
        assert self.done, "Game is not finished yet."
        return self.payout

    def get_game_result(self) -> BinaryGameResult:
        """Maps the payout to a BinaryGameResult."""
        assert self.done, "Game is not finished yet."
        if self.payout > 0:
            return BinaryGameResult(winner=self.agent_ids[0])
        elif self.payout < 0:
            # No official loser agent, but we can say agent 0 lost.
            return BinaryGameResult(winner=None, loser=self.agent_ids[0])
        else:
            return BinaryGameResult(draw=True)

    def validate_action(self, agent_id: int, action: Action) -> bool:
        """Validates if an action is legal for the agent."""
        return action in self.get_agent_actions(agent_id)

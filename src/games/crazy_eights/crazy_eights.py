from dataclasses import dataclass
import random
import logging

from src.games.common import Card, Deck, DiscreteGame, SUITS


@dataclass
class Action:
    """Represents a Crazy Eights action for a single turn.

    A player can either:
    1. Play a card from their hand (``play_card``).
       * If that card is an eight, they **must** specify ``declare_suit``.
    2. Draw a single card from the stock (``draw_card``).
    3. Pass when they cannot act (``is_pass``). Only legal when the stock is empty
       **and** the player has no playable cards.
    """

    play_card: Card | None = None
    declare_suit: str | None = None  # Only required when play_card.rank == "8"
    draw_card: bool = False
    is_pass: bool = False

    def __str__(self):
        if self.play_card is not None:
            suffix = f" declaring {self.declare_suit}" if self.play_card.rank == "8" else ""
            return f"Play {self.play_card}{suffix}"
        if self.draw_card:
            return "Draw"
        if self.is_pass:
            return "Pass"
        return "No-op"

    def __eq__(self, other):  # type: ignore[override]
        """Custom equality that ignores Card instance identity.

        Two Action objects are considered equal when they represent the same
        logical move (same card rank/suit if playing, or identical flags for
        draw/pass) and the same declared suit for wild eights.
        """
        if not isinstance(other, Action):
            return NotImplemented

        # Compare simple flags first – they must all match
        if (
            self.draw_card != other.draw_card
            or self.is_pass != other.is_pass
            or self.declare_suit != other.declare_suit
        ):
            return False

        if self.play_card is None and other.play_card is None:
            return True  # Non-play actions already matched via flags above

        if self.play_card is not None and other.play_card is not None:
            return (
                self.play_card.rank == other.play_card.rank
                and self.play_card.suit == other.play_card.suit
            )

        # One has a card, the other doesn't → not equal
        return False


class CrazyEights(DiscreteGame):

    def __init__(self, agent_ids: list[int], log_events: bool = False):
        super().__init__(agent_ids=agent_ids, game_name="crazy_eights", log_events=log_events)

        # No player limit enforced here – most variants support 2–5 players.

    # ---------------------------------------------------------------------
    # Game initialisation
    # ---------------------------------------------------------------------

    def init_game(self):
        """Deal cards and setup stock / discard piles."""
        deck = Deck()
        cards_per_agent = 5  # Standard Crazy Eights deal size for ≤5 players
        self.hands: dict[int, list[Card]] = {
            aid: deck.deal(cards_per_agent) for aid in self.agent_ids
        }

        # Remaining cards become the stock (draw pile)
        self.stock: list[Card] = deck.deal(len(deck))

        # Create starter card ensuring it's not an eight
        starter = self.stock.pop()
        while starter.rank == "8":
            # Bury the eight roughly in the middle of the remaining stock
            insert_idx = random.randint(0, len(self.stock))
            self.stock.insert(insert_idx, starter)
            starter = self.stock.pop()

        self.discard: list[Card] = [starter]
        self.current_suit: str = starter.suit
        self.current_rank: str = starter.rank

        # Choose random starting agent
        self.current_agent = random.choice(self.agent_ids)

        logging.debug(
            f"CrazyEights initialised - starter {starter}, current suit {self.current_suit},"
            + f" current agent {self.current_agent}"
        )

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def update_current_agent(self):
        self.current_agent = (self.current_agent + 1) % self.num_agents

    # ---------------------------------------------------------------------
    # Core gameplay
    # ---------------------------------------------------------------------

    def step(self, action: Action | None) -> int | None:
        """Advance one turn.

        Returns the ID of the agent whose turn is **next**. If the game has
        ended, returns ``None``.
        """
        assert not self.done, "Cannot take step - game already finished"
        assert action is not None, "Action required"

        self.event_log.push(f"[Agent {self.current_agent}] {action}")

        # Handle DRAW
        if action.draw_card:
            if len(self.stock) == 0:
                raise ValueError("Draw action chosen but stock is empty")
            card = self.stock.pop()
            self.hands[self.current_agent].append(card)
            # Turn ends after drawing
            self.update_current_agent()
            return self.current_agent

        # Handle PASS
        if action.is_pass:
            self.update_current_agent()
            if self._stalemate():
                self.event_log.push("Stalemate reached - counting cards for result")
                self.done = True
                return None
            return self.current_agent

        # Handle PLAY CARD
        card_to_play = action.play_card

        # Verify the player actually has the card
        hand_cards = self.hands[self.current_agent]
        played_card = hand_cards.pop(hand_cards.index(card_to_play))

        # Place card on discard pile
        self.discard.append(played_card)

        # Update current suit / rank context
        if played_card.rank == "8":
            self.current_suit = action.declare_suit  # keep rank as '8'
            self.current_rank = "8"
        else:
            self.current_suit = played_card.suit
            self.current_rank = played_card.rank

        # Check for victory
        if len(self.hands[self.current_agent]) == 0:
            self.done = True
            return None

        # Normal turn end
        self.update_current_agent()
        return self.current_agent

    # ---------------------------------------------------------------------
    # Interfaces for agents
    # ---------------------------------------------------------------------

    def _playable_cards(self, agent_id: int) -> list[Card]:
        """Return the subset of the agent's hand that can legally be played."""
        playable = []
        for card in self.hands[agent_id]:
            if card.rank == "8" or card.suit == self.current_suit or card.rank == self.current_rank:
                playable.append(card)
        return playable

    def get_agent_actions(self, agent_id: int) -> list[Action]:
        actions: list[Action] = []

        # Add play-card actions
        for card in self._playable_cards(agent_id):
            if card.rank == "8":
                for suit in SUITS:
                    actions.append(Action(play_card=card, declare_suit=suit))
            else:
                actions.append(Action(play_card=card))

        # Draw is always allowed if stock not empty
        if len(self.stock) > 0:
            actions.append(Action(draw_card=True))

        # Pass is allowed only when player has no playable cards and stock empty
        if len(actions) == 0 and len(self.stock) == 0:
            actions.append(Action(is_pass=True))
        return actions

    # ---------------------------------------------------------------------
    # Introspection helpers
    # ---------------------------------------------------------------------

    def get_agent_state(self, agent_id: int) -> dict:
        return {
            "hand": self.hands[agent_id],
            "top_discard": self.discard[-1],
            "current_suit": self.current_suit,
            "stock_size": len(self.stock),
        }

    # ---------------------------------------------------------------------
    # Finishing the game
    # ---------------------------------------------------------------------

    def get_agent_scores(self) -> dict[int, float]:
        """Return win/loss or draw outcome.

        Handles victories (including stalemate winner) and draw outcomes.
        """
        assert self.done, "Game not finished yet"
        assert self.num_agents == 2, "get_agent_scores currently supports 2 players only"

        # Decide by fewest cards remaining - works for both stalemate and regular victory
        counts = {aid: len(self.hands[aid]) for aid in self.agent_ids}
        min_count = min(counts.values())
        winners = [aid for aid, cnt in counts.items() if cnt == min_count]

        if len(winners) == 1:
            winner = winners[0]
            return {0: 1.0, 1: 0.0} if winner == 0 else {0: 0.0, 1: 1.0}

        # Equal card counts – draw
        return {0: 0.5, 1: 0.5}

    # ---------------------------------------------------------------------
    # Validation utility
    # ---------------------------------------------------------------------

    def validate_action(self, agent_id: int, action: Action) -> bool:
        """Return True iff the provided action is currently legal for agent."""
        return action in self.get_agent_actions(agent_id)

    def _stalemate(self) -> bool:
        """Return True if stock empty and no agent can play a card."""
        if len(self.stock) > 0:
            return False
        return all(len(self._playable_cards(agent_id)) == 0 for agent_id in self.agent_ids)

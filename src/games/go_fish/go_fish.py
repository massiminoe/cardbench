"""..."""

from dataclasses import dataclass
from collections import Counter
import random

from src.games.common import Deck, DiscreteGame


@dataclass
class Action:
    is_pass: bool = False
    rank: str | None = None
    target_agent_id: int | None = None

    def __str__(self):
        if self.is_pass:
            return "Pass"
        else:
            return f"Rank: {self.rank}, Target: {self.target_agent_id}"


class GoFish(DiscreteGame):

    def __init__(self, agent_ids: list[int], log_events: bool = False):

        super().__init__(agent_ids=agent_ids, game_name="go_fish", log_events=log_events)
        if self.num_agents != 2:
            raise NotImplementedError("Only 2-player Go Fish is supported")

    def init_game(self):

        # Init cards
        deck = Deck()
        if self.num_agents in [2, 3]:
            cards_per_agent = 7
        elif self.num_agents in [4, 5]:
            cards_per_agent = 5
        self.hands = {agent_id: deck.deal(cards_per_agent) for agent_id in self.agent_ids}
        self.books: dict[int, list[str]] = {agent_id: [] for agent_id in self.agent_ids}  # Ranks
        self.stock = deck.deal(len(deck))  # Remaining cards

        self.current_agent = random.choice(self.agent_ids)
        self.total_books = 0  # Game ends at 13

    def update_current_agent(self):
        self.current_agent = (self.current_agent + 1) % self.num_agents

    def step(self, action: Action | None) -> int:
        """
        :return: current_agent
        """

        self.event_log.push(f"[Agent {self.current_agent}] {action}")

        if action.is_pass:
            self.update_current_agent()
            return self.current_agent

        # Does target have this rank?
        target_ranks = set(card.rank for card in self.hands[action.target_agent_id])
        if action.rank not in target_ranks:
            self.event_log.push(f"[Agent {self.current_agent}] Gone fishing")
            if len(self.stock) > 0:
                card = self.stock.pop()
                self.hands[self.current_agent].append(card)
        else:
            stolen_cards = []
            new_target_hand = []
            for card in self.hands[action.target_agent_id]:
                if card.rank == action.rank:
                    stolen_cards.append(card)
                else:
                    new_target_hand.append(card)
            self.hands[action.target_agent_id] = new_target_hand
            self.hands[self.current_agent].extend(stolen_cards)
            self.event_log.push(f"[Agent {self.current_agent}] Caught {len(stolen_cards)} cards")

        # Check for new books
        rank_counts = Counter(card.rank for card in self.hands[self.current_agent])
        for rank, count in rank_counts.items():
            if count == 4:
                self.books[self.current_agent].append(rank)
                self.hands[self.current_agent] = [
                    card for card in self.hands[self.current_agent] if card.rank != rank
                ]
                self.total_books += 1
                self.event_log.push(f"[Agent {self.current_agent}] Made a book of {rank}")

        # Check if done
        if self.total_books == 13:
            self.done = True
            return None

        # Update turn
        self.update_current_agent()
        return self.current_agent

    def get_agent_actions(self, agent_id: int) -> list[Action]:
        """
        Returns a list of legal actions for the given agent.
        """
        actions = []
        ranks = set(card.rank for card in self.hands[agent_id])
        for rank in ranks:
            for target_agent_id in self.agent_ids:
                if target_agent_id == agent_id:
                    continue
                actions.append(Action(rank=rank, target_agent_id=target_agent_id))
        if len(actions) == 0:
            actions.append(Action(is_pass=True))
        return actions

    def get_agent_state(self, agent_id: int) -> dict:
        """
        :return: state
        """
        return {
            "hand": self.hands[agent_id],
            "books": self.books[agent_id],
        }

    def get_agent_scores(self) -> dict[int, float]:
        """Player with the most books wins."""
        assert self.num_agents == 2, "Implementation for get_agent_scores only supports 2 players"
        assert self.done, "Game must be done to get a result"
        agent_0_books = len(self.books[0])
        agent_1_books = len(self.books[1])
        if agent_0_books > agent_1_books:
            return {0: 1.0, 1: 0.0}
        elif agent_0_books < agent_1_books:
            return {0: 0.0, 1: 1.0}
        else:  # Draw
            return {0: 0.5, 1: 0.5}

    def validate_action(self, agent_id: int, action: Action) -> bool:
        """..."""
        return action in self.get_agent_actions(agent_id)

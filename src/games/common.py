import random
from dataclasses import dataclass
from typing import Any

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
SUITS = ["C", "D", "H", "S"]


@dataclass
class Card:

    rank: str
    suit: str

    def __str__(self):
        return f"{self.rank}{self.suit}"


class Deck:

    def __init__(self, shuffle=True):

        self.cards = [Card(rank, suit) for rank in RANKS for suit in SUITS]
        if shuffle:
            self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards: int):
        return [self.cards.pop() for _ in range(num_cards)]

    def __len__(self):

        return len(self.cards)


@dataclass
class BinaryGameResult:

    draw: bool = False
    winner: int | None = None
    loser: int | None = None


class EventLog:

    def __init__(self, log_events: bool):
        self.events: list[str] = []
        self.log_events = log_events

    def push(self, event: str):
        self.events.append(event)
        if self.log_events:
            print(event)

    def get_events_from(self, idx: int) -> list[str]:
        return self.events[idx:]
    
    def __len__(self):
        return len(self.events)


class DiscreteGame:
    """
    Game with a discrete action space.
    """

    def __init__(self, agent_ids: list[int], log_events: bool = False):
        self.agent_ids = agent_ids
        self.num_agents = len(agent_ids)
        self.current_agent: int = None
        self.event_log: EventLog = EventLog(log_events)
        self.done = False
        # TODO - random state initialization

    def init_game(self):
        pass

    def step(self, action: Any) -> int:
        """
        :return: current_agent
        """
        pass

    def get_agent_actions(self, agent_id: int) -> list[Any]:
        """..."""

    def get_agent_state(self, agent_id: int) -> dict:
        """..."""
        pass

    def get_game_result(self) -> BinaryGameResult:
        """..."""
        pass

    def validate_action(self, action: Any) -> bool:
        """..."""
        pass

import random
from dataclasses import dataclass
from typing import Any
import logging
from enum import Enum

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
SUITS = ["C", "D", "H", "S"]

logger = logging.getLogger(__name__)


@dataclass
class Card:

    rank: str
    suit: str

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def __repr__(self):
        return f"'{self}'"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))


class Deck:

    def __init__(self, shuffle=True):

        self.cards = [Card(rank, suit) for rank in RANKS for suit in SUITS]
        if shuffle:
            self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards: int):
        return [self.cards.pop() for _ in range(num_cards)]

    def deal_with_replacement(self, num_cards: int):
        return random.choices(self.cards, k=num_cards)

    def __len__(self):

        return len(self.cards)


class Winner(Enum):
    AGENT_0 = "agent_0"
    AGENT_1 = "agent_1"
    DRAW = "draw"


@dataclass
class GameResult:
    """Detailed game result with agent names and scores, to be persisted."""

    agent_0_name: str
    agent_1_name: str
    agent_0_score: float
    agent_1_score: float
    event_log: list[str]
    details: str | None = None


class EventLog:

    def __init__(self, log_events: bool):
        self.events: list[str] = []
        self.log_events = log_events

    def push(self, event: str):
        self.events.append(event)
        if self.log_events:
            logger.info(event)

    def get_events_from(self, idx: int) -> list[str]:
        return self.events[idx:]

    def __len__(self):
        return len(self.events)


class DiscreteGame:
    """
    Game with a discrete action space.
    """

    def __init__(self, agent_ids: list[int], game_name: str, log_events: bool = False):
        self.agent_ids = agent_ids
        self.num_agents = len(agent_ids)
        self.current_agent: int = None
        self.event_log: EventLog = EventLog(log_events)
        self.done = False
        self.game_name = game_name
        self.rules = self.load_rules()
        # TODO - random state initialization

    def load_rules(self) -> str:
        """
        Load the rules of the game from a file.
        """
        with open(f"src/games/{self.game_name}/rules.md", "r") as f:
            return f.read()

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

    def get_agent_scores(self) -> dict[int, float]:
        """At the end of the game, get the scores for each agent."""
        pass

    def validate_action(self, action: Any) -> bool:
        """..."""
        pass

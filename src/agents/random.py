import random
from typing import Any

from src.agents.common import DiscreteAgent


class RandomAgent(DiscreteAgent):

    def get_action(self, new_events: list[str], state: dict, actions: list[Any]) -> Any:
        return random.choice(actions)

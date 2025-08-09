from dataclasses import dataclass
from typing import Any


@dataclass
class ActionResponseFormat:
    thoughts: str
    action_index: int


class DiscreteAgent:

    def __init__(self, agent_id: int, game_name: str, rules: str):
        self.agent_id = agent_id
        self.game_name = game_name
        self.rules = rules

    def get_action(self, new_events: list[str], state: dict, actions: list[Any]) -> Any:
        pass

    def get_name(self) -> str:
        return f"{self.__class__.__name__}"

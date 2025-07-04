from typing import Any


class DiscreteAgent:

    def __init__(self, agent_id: int):
        self.agent_id = agent_id

    def get_action(self, new_events: list[str], state: dict, actions: list[Any]) -> Any:
        pass
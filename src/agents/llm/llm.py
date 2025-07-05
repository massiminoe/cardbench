import json
from typing import Any
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.agents.common import ActionResponseFormat, DiscreteAgent

load_dotenv()

CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MISTRAL_SMALL_FREE = "mistralai/mistral-small-3.2-24b-instruct:free"
MISTRAL_SMALL = "mistralai/mistral-small-3.2-24b-instruct"
QWEN3_14B_FREE = "qwen/qwen3-14b:free"


class LLMAgent(DiscreteAgent):

    def __init__(self, agent_id: int, game_name: str, rules: str, model_id: str = MISTRAL_SMALL):
        super().__init__(agent_id, game_name, rules)
        with open(f"src/agents/llm/system_prompt_template.txt", "r") as f:
            system_prompt_template = f.read()
            self.system_prompt = system_prompt_template.format(game_name=game_name, rules=rules)
        with open(f"src/agents/llm/user_prompt_template.txt", "r") as f:
            self.user_prompt_template = f.read()
        self.model_id = model_id
        self.init_messages()

    def init_messages(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def build_user_prompt(self, new_events: list[str], state: dict, actions: list[Any]) -> str:
        actions_formatted = "\n".join([f"{i}: {action}" for i, action in enumerate(actions)])
        return self.user_prompt_template.format(
            events=new_events, state=state, actions=actions_formatted
        )

    def _clean_json(self, content: str) -> str:
        """Strip optional markdown code fences (``` or ```json) from the model response."""
        content = content.strip()
        if content.startswith("```"):
            # Drop the opening fence line (could be ``` or ```json)
            content = "\n".join(content.split("\n")[1:])
            # Remove optional closing fence
            if content.endswith("```"):
                content = "\n".join(content.split("\n")[:-1])
        return content.strip()

    def invoke_llm(self, user_prompt: str) -> ActionResponseFormat:
        self.messages.append({"role": "user", "content": user_prompt})
        response = CLIENT.chat.completions.create(
            model=self.model_id,
            messages=self.messages,
            response_format={"type": "json_object"},
        )
        response_message = response.choices[0].message
        self.messages.append(response_message)
        raw_content = response_message.content
        print(raw_content)
        cleaned_content = self._clean_json(raw_content)
        return ActionResponseFormat(**json.loads(cleaned_content))

    def get_action(self, new_events: list[str], state: dict, actions: list[Any]) -> Any:
        user_prompt = self.build_user_prompt(new_events, state, actions)
        response = self.invoke_llm(user_prompt)
        return actions[response.action_index]

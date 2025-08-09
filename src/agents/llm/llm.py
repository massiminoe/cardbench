import json
from typing import Any
import os
import logging

from dotenv import load_dotenv

# Always available base client (declared dependency)
from openai import OpenAI as BaseOpenAI

from src.agents.common import ActionResponseFormat, DiscreteAgent

load_dotenv()


def _env_flag_is_true(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


# Decide which OpenAI client to use based on a simple env flag and availability
if _env_flag_is_true("ENABLE_LANGFUSE"):
    try:
        from langfuse.openai import OpenAI as OpenAIClient  # type: ignore

        logging.info("Using Langfuse OpenAI client.")
    except ImportError:
        logging.info("Langfuse not installed; using standard OpenAI client.")
        OpenAIClient = BaseOpenAI
else:
    logging.info("Langfuse disabled; using standard OpenAI client.")
    OpenAIClient = BaseOpenAI


CLIENT = OpenAIClient(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MISTRAL_SMALL_FREE = "mistralai/mistral-small-3.2-24b-instruct:free"
MISTRAL_SMALL = "mistralai/mistral-small-3.2-24b-instruct"
QWEN3_14B_FREE = "qwen/qwen3-14b:free"
OPENAI_GPT_4_1_MINI = "openai/gpt-4.1-mini"

DEFAULT_MODEL = OPENAI_GPT_4_1_MINI


class LLMAgent(DiscreteAgent):

    def __init__(self, agent_id: int, game_name: str, rules: str, model_id: str = DEFAULT_MODEL):
        super().__init__(agent_id, game_name, rules)
        with open(f"src/agents/llm/system_prompt_template.txt", "r") as f:
            system_prompt_template = f.read()
            self.system_prompt = system_prompt_template.format(
                game_name=game_name, rules=rules, agent_id=agent_id
            )
        with open(f"src/agents/llm/user_prompt_template.txt", "r") as f:
            self.user_prompt_template = f.read()
        self.model_id = model_id
        self.init_messages()

    def get_name(self) -> str:
        return f"LLMAgent_{self.model_id}"

    def init_messages(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def build_user_prompt(self, new_events: list[str], state: dict, actions: list[Any]) -> str:
        actions_formatted = "\n".join([f"{i}: {action}" for i, action in enumerate(actions)])
        events_formatted = "\n".join([f"{i}: {event}" for i, event in enumerate(new_events)])
        return self.user_prompt_template.format(
            events=events_formatted, state=state, actions=actions_formatted
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
        cleaned_content = self._clean_json(raw_content)
        return ActionResponseFormat(**json.loads(cleaned_content))

    def get_action(self, new_events: list[str], state: dict, actions: list[Any]) -> Any:
        user_prompt = self.build_user_prompt(new_events, state, actions)
        response = self.invoke_llm(user_prompt)
        return actions[response.action_index]

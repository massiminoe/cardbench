import logging
import datetime as dt
import json
import os

from src.games.common import DiscreteGame, GameResult
from src.agents.common import DiscreteAgent

logger = logging.getLogger(__name__)

MAX_ERROR_COUNT = 3
MAX_TURN_COUNT = 50


def run_discrete_game(
    game_cls: type[DiscreteGame],
    agents_0_cls: type[DiscreteAgent],
    agents_1_cls: type[DiscreteAgent],
    agent_0_kwargs: dict = {},
    agent_1_kwargs: dict = {},
    log_events: bool = False,
) -> GameResult:
    """
    Run a discrete game between exactly two agents.
    """
    # Initialisation
    agent_ids = [0, 1]
    game = game_cls(agent_ids, log_events)
    game.init_game()
    agent_0 = agents_0_cls(0, game.game_name, game.rules, **agent_0_kwargs)
    agent_1 = agents_1_cls(1, game.game_name, game.rules, **agent_1_kwargs)
    agents = [agent_0, agent_1]

    # Keep track of which events have been pushed to the agent
    agent_event_idxs = {agent_id: 0 for agent_id in agent_ids}
    agent_error_counts = {agent_id: 0 for agent_id in agent_ids}

    # Play!
    logger.info(
        f"Playing {game.game_name} between {agent_0.get_name()} and {agent_1.get_name()}..."
    )
    turn_count = 0
    while not game.done:
        turn_count += 1
        if turn_count >= MAX_TURN_COUNT * game.num_agents:
            logger.info(f"Game ended in draw after reaching max turn count ({MAX_TURN_COUNT})")
            return GameResult(
                agent_0_name=agent_0.get_name(),
                agent_1_name=agent_1.get_name(),
                agent_0_score=0.5,
                agent_1_score=0.5,
                event_log=game.event_log.events,
                details=f"Game ended in draw after reaching max turn count ({MAX_TURN_COUNT})",
            )

        # Gather info
        current_agent = game.current_agent
        new_events = game.event_log.get_events_from(agent_event_idxs[current_agent])
        agent_event_idxs[current_agent] = len(game.event_log)
        agent_actions = game.get_agent_actions(current_agent)
        agent_state = game.get_agent_state(current_agent)

        # Get action
        try:
            action = agents[current_agent].get_action(new_events, agent_state, agent_actions)
            if not game.validate_action(current_agent, action):
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            agent_error_counts[current_agent] += 1

            # This agent loses
            if agent_error_counts[current_agent] > MAX_ERROR_COUNT:
                if current_agent == 0:
                    agent_0_score = 0
                else:
                    agent_0_score = 1
                agent_1_score = 1 - agent_0_score
                return GameResult(
                    agent_0_name=agent_0.get_name(),
                    agent_1_name=agent_1.get_name(),
                    agent_0_score=agent_0_score,
                    agent_1_score=agent_1_score,
                    event_log=game.event_log.events,
                    details=f"Agent {current_agent} reached max error count ({MAX_ERROR_COUNT})",
                )

            # Return first action
            action = agent_actions[0]
            logger.debug(f"Agent {current_agent} error: {e}")

        # Step
        game.step(action)

    # Game over
    agent_scores = game.get_agent_scores()
    return GameResult(
        agent_0_name=agent_0.get_name(),
        agent_1_name=agent_1.get_name(),
        agent_0_score=agent_scores[0],
        agent_1_score=agent_scores[1],
        event_log=game.event_log.events,
        details=f"Game ended after {turn_count} turns",
    )


def run_and_save_discrete_game(
    game_cls: type[DiscreteGame],
    agents_0_cls: type[DiscreteAgent],
    agents_1_cls: type[DiscreteAgent],
    agent_0_kwargs: dict = {},
    agent_1_kwargs: dict = {},
    log_events: bool = False,
    results_dir: str = "./results",
) -> GameResult:
    """
    Run a discrete game and save the results.
    """
    # Run the game...
    game_result = run_discrete_game(
        game_cls, agents_0_cls, agents_1_cls, agent_0_kwargs, agent_1_kwargs, log_events
    )

    # Save the game...
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    game_id = f"{game_cls.__name__}_{agents_0_cls.__name__}_{agents_1_cls.__name__}_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    with open(f"{results_dir}/{game_id}.json", "w") as f:
        json.dump(game_result.__dict__, f)
    return game_result

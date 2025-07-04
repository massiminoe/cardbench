from src.games.common import DiscreteGame
from src.agents.common import DiscreteAgent


def run_discrete_game(
    game_cls: type[DiscreteGame], agents: list[DiscreteAgent], log_events: bool = False
):
    """
    Run a discrete game.
    """
    # Initialisation
    agent_ids = [i for i in range(len(agents))]
    game = game_cls(agent_ids, log_events)
    game.init_game()
    # Keep track of which events have been pushed to the agent
    agent_event_idxs = {agent_id: 0 for agent_id in agent_ids}
    agent_error_counts = {agent_id: 0 for agent_id in agent_ids}

    # Play!
    while not game.done:
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
            action = agent_actions[0]
            continue

        # Step
        game.step(action)

    # Game over
    game_result = game.get_game_result()
    return game_result

import logging

from src.games.common import DiscreteGame
from src.agents.common import DiscreteAgent

def run_discrete_game(
    game_cls: type[DiscreteGame], agents_cls: list[type[DiscreteAgent]], log_events: bool = False
):
    """
    Run a discrete game.
    """
    # Initialisation
    agent_ids = [i for i in range(len(agents_cls))]
    game = game_cls(agent_ids, log_events)
    game.init_game()
    agents = [
        agent_cls(agent_id, game.game_name, game.rules)
        for agent_id, agent_cls in enumerate(agents_cls)
    ]
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
            logging.exception(f"Agent {current_agent} error: {e}")

        # Step
        game.step(action)

    # Game over
    game_result = game.get_game_result()
    return game_result


def run_blackjack_tournament(
    agents_cls: list[type[DiscreteAgent]], n_games: int, log_events: bool = False
):
    """
    Run a blackjack tournament between two agents.
    Each agent plays n_games against the dealer, and the agent with the higher
    total payout wins.
    """
    from src.games.blackjack.blackjack import Blackjack, ActionType, Action

    payouts = {0: 0.0, 1: 0.0}

    for agent_id, agent_cls in enumerate(agents_cls):
        agent = agent_cls(agent_id, "blackjack", "")  # Rules can be empty for now

        for _ in range(n_games):
            game = Blackjack(agent_ids=[agent_id], log_events=log_events)
            game.init_game()

            while not game.done:
                agent_state = game.get_agent_state(agent_id)
                agent_actions = game.get_agent_actions(agent_id)

                if not agent_actions:  # No actions available, game must be over
                    break

                # For blackjack, let's assume a simple policy for non-LLM agents
                # or get action from LLM agent.
                # This part can be improved with a more sophisticated agent interface.
                if hasattr(agent, "llm"):
                    action = agent.get_action([], agent_state, agent_actions)
                else:
                    # Simple heuristic: stand on 17 or more.
                    player_value = game._get_hand_value(agent_state["player_hand"])
                    if player_value >= 17:
                        action = Action(ActionType.STAND)
                    else:
                        action = Action(ActionType.HIT)
                
                if not game.validate_action(agent_id, action):
                    # Fallback to a valid action if agent's choice is invalid
                    action = agent_actions[0]

                game.step(action)

            payouts[agent_id] += game.get_payout()

    logging.info(f"Tournament finished. Payouts: {payouts}")

    if payouts[0] > payouts[1]:
        return {"winner": 0, "loser": 1, "payouts": payouts}
    elif payouts[1] > payouts[0]:
        return {"winner": 1, "loser": 0, "payouts": payouts}
    else:
        return {"draw": True, "payouts": payouts}

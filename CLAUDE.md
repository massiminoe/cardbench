# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

The project uses a Makefile for common tasks:

- `make main` - Run a single game between two agents (currently Gin Rummy with RandomAgent vs LLMAgent)
- `make run_tournament` - Run a tournament with multiple agents and games
- `make test` - Run the test suite using pytest

Python execution requires setting `PYTHONPATH=.` to properly import modules from the `src/` directory.

## Architecture Overview

This is a card game benchmarking framework for evaluating AI agents. The architecture follows a modular design:

### Core Components

- **Games**: Located in `src/games/`, each game inherits from `DiscreteGame` base class
  - Each game has its own subdirectory with implementation and rules.md file
  - Supported games: Gin Rummy, Crazy Eights, Go Fish, Blackjack (placeholder)
  - Games manage state, validate actions, and track event logs

- **Agents**: Located in `src/agents/`, inherit from `DiscreteAgent` base class
  - `RandomAgent`: Makes random valid moves
  - `LLMAgent`: Uses OpenAI-compatible API (via OpenRouter) with structured JSON responses
  - LLM agents use system/user prompt templates from `src/agents/llm/`

- **Controller**: `src/controller.py` orchestrates game execution
  - `run_discrete_game()`: Runs a single game between two agents
  - `run_and_save_discrete_game()`: Runs game and saves results to JSON
  - Handles error recovery (max 3 errors per agent) and turn limits (max 50 turns per agent)

- **Tournament**: `src/tournament.py` runs multiple games in parallel
  - Configurable agent lists with different LLM models
  - Round-robin tournament format
  - Results saved to timestamped directories in `results/`

### Key Design Patterns

- **Event-driven**: Games maintain event logs that agents receive for context
- **Action validation**: All agent actions are validated before execution
- **Error handling**: Agents that exceed error limits automatically lose
- **Persistence**: All game results saved as JSON with full event logs and metadata

### Environment Configuration

- Uses python-dotenv for environment variables
- OpenRouter API key required: `OPENROUTER_API_KEY`
- Optional Langfuse tracing: `ENABLE_LANGFUSE=true` (requires langfuse package)
- LLM agent uses structured JSON response format via OpenAI API

### Testing

- Tests use pytest with parametrized test cases across all games
- Fixed random seeds for reproducible test results
- Integration tests verify game completion and result format

The framework is designed for extensibility - new games implement the `DiscreteGame` interface, and new agents implement the `DiscreteAgent` interface.
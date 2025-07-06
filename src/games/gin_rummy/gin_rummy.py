from dataclasses import dataclass
from collections import defaultdict
import random
import logging
from itertools import combinations
from enum import Enum, auto

from src.games.common import Card, Deck, DiscreteGame, BinaryGameResult


class ActionType(Enum):
    DRAW_FROM_STOCK = auto()
    DRAW_FROM_DISCARD = auto()
    TAKE_UPCARD = auto()
    PASS_UPCARD = auto()
    DISCARD = auto()
    KNOCK = auto()
    GIN = auto()


@dataclass
class Action:
    """Represents a single move in Gin Rummy."""
    action_type: ActionType
    card: Card | None = None  # Used for DISCARD, KNOCK

    def __str__(self):
        if self.card:
            return f"{self.action_type.name}({self.card})"
        return self.action_type.name

    def __eq__(self, other):
        if not isinstance(other, Action):
            return NotImplemented
        
        return self.action_type == other.action_type and self.card == other.card


class GinRummy(DiscreteGame):
    
    def __init__(self, agent_ids: list[int], log_events: bool = False):
        super().__init__(agent_ids=agent_ids, game_name="gin_rummy", log_events=log_events)
        if self.num_agents != 2:
            raise NotImplementedError("Only 2-player Gin Rummy is supported")
    
    def init_game(self):
        """Deal 10 cards to each player, create stock and discard piles."""
        deck = Deck()
        
        # Deal 10 cards to each player
        self.hands = {agent_id: deck.deal(10) for agent_id in self.agent_ids}
        
        # Remaining cards become stock
        self.stock = deck.deal(len(deck))
        
        # Flip top card to start discard pile
        self.discard = [self.stock.pop()]
        
        # Game starts with upcard phase
        self.phase = "upcard_draw"  # Phases: upcard_draw, upcard_discard, draw, discard
        self.current_agent = random.choice(self.agent_ids)
        self.upcard_passed_by = set()  # Track who passed on upcard
        
        logging.debug(f"GinRummy initialized - upcard {self.discard[-1]}, starting agent {self.current_agent}")
    
    def step(self, action: Action | None) -> int | None:
        """Process one turn action."""
        assert not self.done, "Cannot take step - game already finished"
        assert action is not None, "Action required"
        
        self.event_log.push(f"[Agent {self.current_agent}] {action}")
        
        # Handle upcard phase
        if self.phase == "upcard_draw":
            if action.action_type == ActionType.TAKE_UPCARD:
                # Player takes upcard, now must discard
                upcard = self.discard.pop()
                self.hands[self.current_agent].append(upcard)
                self.phase = "upcard_discard"
                
            elif action.action_type == ActionType.PASS_UPCARD:
                self.upcard_passed_by.add(self.current_agent)
                self.update_current_agent()
                
                # If both players passed, first player must draw from stock
                if len(self.upcard_passed_by) == 2:
                    self.phase = "draw"
            
            return self.current_agent

        elif self.phase == "upcard_discard":
            # Player took upcard, now must discard
            if action.action_type == ActionType.DISCARD and action.card:
                self._discard_card(action.card)
                # Check for knock/gin, otherwise continue
                if self._can_gin():
                    self._end_game_gin()
                    return None
                if self._can_knock():
                    self._end_game_knock()
                    return None
                
                # If stock is depleted, game is a draw
                if len(self.stock) <= 2:
                    self._end_game_stock_empty()
                    return None

                self.phase = "draw"
                self.update_current_agent()
            
            return self.current_agent

        # Handle normal play phase
        elif self.phase == "draw":
            # Player must draw a card
            if action.action_type == ActionType.DRAW_FROM_STOCK:
                card = self.stock.pop()
                self.hands[self.current_agent].append(card)
                self.phase = "discard"

            elif action.action_type == ActionType.DRAW_FROM_DISCARD:
                card = self.discard.pop()
                self.hands[self.current_agent].append(card)
                self.phase = "discard"
            
            return self.current_agent
            
        elif self.phase == "discard":
            # Player has drawn, must now discard, knock, or gin
            if action.action_type == ActionType.DISCARD and action.card:
                self._discard_card(action.card)

                # If stock is depleted, game is a draw
                if len(self.stock) <= 2:
                    self._end_game_stock_empty()
                    return None
                
                self.phase = "draw"
                self.update_current_agent()
            
            elif action.action_type == ActionType.KNOCK and action.card:
                # Must discard before knocking
                self._discard_card(action.card)
                self._end_game_knock()
                return None

            elif action.action_type == ActionType.GIN and action.card:
                # Must discard before going gin
                self._discard_card(action.card)
                self._end_game_gin()
                return None
        
        return self.current_agent
    
    def _discard_card(self, card: Card):
        """Remove card from current player's hand and add to discard pile."""
        hand = self.hands[self.current_agent]
        hand.remove(card)
        self.discard.append(card)
    
    def _can_gin(self) -> bool:
        """Check if current player can go gin (all cards in valid combinations)."""
        hand = self.hands[self.current_agent]
        if len(hand) != 11:
            return False

        # Check if any 10-card subset is a gin hand
        for card_to_discard in hand:
            temp_hand = hand[:]
            temp_hand.remove(card_to_discard)
            if self._get_unmatched_points(temp_hand) == 0:
                return True
        return False
    
    def _can_knock(self) -> bool:
        """Check if current player can knock (unmatched points <= 10)."""
        hand = self.hands[self.current_agent]
        if len(hand) != 11:
            return False

        # Check if any 10-card subset is a knock-able hand
        for card_to_discard in hand:
            temp_hand = hand[:]
            temp_hand.remove(card_to_discard)
            unmatched_points = self._get_unmatched_points(temp_hand)
            if 0 < unmatched_points <= 10:
                return True
        return False
    
    def _end_game_gin(self):
        """End game with gin."""
        self.done = True
        self.winner = self.current_agent
        self.event_log.push(f"Agent {self.current_agent} goes Gin!")
    
    def _end_game_knock(self):
        """End game with knock."""
        self.done = True
        knocker = self.current_agent
        opponent = 1 - knocker
        
        knocker_points = self._get_unmatched_points(self.hands[knocker])
        opponent_points = self._get_unmatched_points(self.hands[opponent])
        
        if knocker_points < opponent_points:
            self.winner = knocker
        else:
            self.winner = opponent  # Undercut
            
        self.event_log.push(f"Agent {knocker} knocks with {knocker_points} points, "
                           f"Agent {opponent} has {opponent_points} points")
    
    def _end_game_stock_empty(self):
        """End game when stock is empty. Player with fewest points wins."""
        self.done = True
        
        player_0_id = self.agent_ids[0]
        player_1_id = self.agent_ids[1]

        player_0_points = self._get_unmatched_points(self.hands[player_0_id])
        player_1_points = self._get_unmatched_points(self.hands[player_1_id])

        self.event_log.push(f"Stock empty. Agent {player_0_id} has {player_0_points} points, "
                           f"Agent {player_1_id} has {player_1_points} points.")
        
        if player_0_points < player_1_points:
            self.winner = player_0_id
        elif player_1_points < player_0_points:
            self.winner = player_1_id
        else:
            # It's a draw, winner remains None
            self.event_log.push("Game is a draw.")

    def _get_rank_sort_value(self, card: Card) -> int:
        """Get the numerical sort value for a card's rank (Ace low)."""
        if card.rank.isdigit():
            return int(card.rank)
        return {'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 1}[card.rank]

    def _get_card_value(self, card: Card) -> int:
        """Return the point value of a single card."""
        if card.rank in ['T', 'K', 'Q', 'J']:
            return 10
        if card.rank == 'A':
            return 1
        return int(card.rank)
    
    def _get_all_melds(self, hand: list[Card]) -> list[list[Card]]:
        """Find all possible sets and runs in a hand."""
        melds = []
        
        # Find sets (3 or 4 of a kind)
        by_rank = defaultdict(list)
        for card in hand:
            by_rank[card.rank].append(card)
        
        for rank in by_rank:
            cards_of_rank = by_rank[rank]
            if len(cards_of_rank) == 3:
                melds.append(cards_of_rank)
            elif len(cards_of_rank) == 4:
                # Add the 4-card set
                melds.append(cards_of_rank)
                # Add all possible 3-card subsets
                for combo in combinations(cards_of_rank, 3):
                    melds.append(list(combo))

        # Find runs (3+ sequential cards of same suit)
        by_suit = defaultdict(list)
        for card in hand:
            by_suit[card.suit].append(card)
        
        for suit in by_suit:
            cards = sorted(by_suit[suit], key=self._get_rank_sort_value)
            if len(cards) < 3:
                continue
                
            for i in range(len(cards) - 2):
                for j in range(i + 2, len(cards)):
                    run = cards[i:j+1]
                    # Ace-high runs are invalid
                    if run[-1].rank == 'A' and run[-2].rank == 'K':
                        continue
                        
                    is_run = True
                    for k in range(len(run) - 1):
                        if self._get_rank_sort_value(run[k+1]) != self._get_rank_sort_value(run[k]) + 1:
                            is_run = False
                            break
                    if is_run:
                        melds.append(run)
        
        return melds
        
    def _get_unmatched_points(self, hand: list[Card]) -> int:
        """Recursively find the minimum deadwood points in a hand."""
        memo = {}
        
        def get_min_points(current_hand_tuple: tuple[Card, ...]) -> int:
            if not current_hand_tuple:
                return 0
            
            if current_hand_tuple in memo:
                return memo[current_hand_tuple]

            current_hand_list = list(current_hand_tuple)
            
            # Base case: score of hand with no melds
            min_points = sum(self._get_card_value(c) for c in current_hand_list)
            
            # Find all possible melds in the current hand
            possible_melds = self._get_all_melds(current_hand_list)
            
            for meld in possible_melds:
                # Create the remaining hand after using this meld
                remaining_hand = current_hand_list[:]
                for card in meld:
                    remaining_hand.remove(card)
                
                # Recursively find the score of the rest of the hand
                # Sort by suit then rank to create a canonical tuple for memoization
                key = tuple(sorted(remaining_hand, key=lambda c: (c.suit, self._get_rank_sort_value(c))))
                meld_score = get_min_points(key)
                min_points = min(min_points, meld_score)
            
            memo[current_hand_tuple] = min_points
            return min_points
            
        # Initial call with the sorted tuple of the hand
        initial_key = tuple(sorted(hand, key=lambda c: (c.suit, self._get_rank_sort_value(c))))
        return get_min_points(initial_key)
    
    def _get_optimal_meld_combination(self, hand: list[Card]) -> list[list[Card]]:
        """Find the combination of melds that results in the minimum deadwood points."""
        
        # Find all melds
        melds = self._get_all_melds(hand)
        
        # Find all combinations of non-overlapping melds
        meld_combos = []
        for i in range(1, len(melds) + 1):
            for combo in combinations(melds, i):
                # Check for overlapping cards
                flat_list = [card for meld in combo for card in meld]
                if len(flat_list) == len(set(flat_list)):
                    meld_combos.append(combo)
                    
        # Start with the case of no melds, where deadwood is the whole hand
        min_points = sum(self._get_card_value(c) for c in hand)
        best_melds_combo = []

        for combo in meld_combos:
            melded_cards = {card for meld in combo for card in meld}
            
            current_points = 0
            for card in hand:
                if card not in melded_cards:
                    current_points += self._get_card_value(card)

            if current_points <= min_points:
                min_points = current_points
                best_melds_combo = list(combo)
        
        return best_melds_combo

    def _get_unmatched_cards(self, hand: list[Card]) -> list[Card]:
        """Find the specific cards that are unmatched when minimizing deadwood points."""
        
        best_melds = self._get_optimal_meld_combination(hand)
        
        # Get the cards that are not in the best meld combination
        melded_cards = {card for meld in best_melds for card in meld}
        unmatched = [card for card in hand if card not in melded_cards]
        
        return unmatched
    
    def update_current_agent(self):
        """Switch to the next player."""
        self.current_agent = (self.current_agent + 1) % self.num_agents
    
    def get_agent_actions(self, agent_id: int) -> list[Action]:
        """Return list of valid actions for the given agent."""
        if agent_id != self.current_agent:
            return []
            
        actions = []
        hand = self.hands[agent_id]
        
        if self.phase == "upcard_draw":
            # Can take upcard or pass
            if len(self.discard) > 0:
                actions.append(Action(action_type=ActionType.TAKE_UPCARD))
            actions.append(Action(action_type=ActionType.PASS_UPCARD))
            
        elif self.phase == "upcard_discard" or self.phase == "discard":
            # Can discard any card from hand
            for card in hand:
                actions.append(Action(action_type=ActionType.DISCARD, card=card))
            
            # Can also knock or go gin if conditions are met
            gin_discards = []
            knock_discards = []

            if len(hand) == 11:
                for card_to_discard in hand:
                    temp_hand = hand[:]
                    temp_hand.remove(card_to_discard)
                    points = self._get_unmatched_points(temp_hand)
                    if points == 0:
                        gin_discards.append(card_to_discard)
                    elif 0 < points <= 10:
                        knock_discards.append(card_to_discard)
            
            if gin_discards:
                for card in gin_discards:
                    actions.append(Action(action_type=ActionType.GIN, card=card))
            elif knock_discards:
                for card in knock_discards:
                    actions.append(Action(action_type=ActionType.KNOCK, card=card))

        elif self.phase == "draw":
            # Can draw from stock or discard pile
            if len(self.stock) > 2:
                actions.append(Action(action_type=ActionType.DRAW_FROM_STOCK))
            if len(self.discard) > 0:
                actions.append(Action(action_type=ActionType.DRAW_FROM_DISCARD))
        
        return actions
    
    def get_agent_state(self, agent_id: int) -> dict:
        """Return observable state for the given agent."""
        hand = self.hands[agent_id]
        return {
            "hand": hand,
            "top_discard": self.discard[-1] if self.discard else None,
            "stock_size": len(self.stock),
            "phase": self.phase,
            "best_melds": self._get_optimal_meld_combination(hand),
            "unmatched_points": self._get_unmatched_points(hand),
        }
    
    def get_game_result(self) -> BinaryGameResult:
        """Return the game result."""
        assert self.done, "Game not finished yet"
        
        # Check if game ended in draw (stock empty)
        if not hasattr(self, 'winner'):
            return BinaryGameResult(draw=True)
        
        # Return winner/loser
        winner = self.winner
        loser = 1 - winner
        return BinaryGameResult(winner=winner, loser=loser)
    
    def validate_action(self, agent_id: int, action: Action) -> bool:
        """Check if action is valid for the given agent."""
        return action in self.get_agent_actions(agent_id)

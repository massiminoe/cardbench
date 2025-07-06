import pytest
from src.games.common import Card
from src.games.gin_rummy.gin_rummy import GinRummy, Action, ActionType

# Helper to create cards from strings like "5H", "KS", "AC"
def C(card_str: str) -> Card:
    rank_map = {'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10'}
    
    rank_char = card_str[:-1]
    suit_char = card_str[-1]
    
    rank = rank_map.get(rank_char, rank_char)
    
    suit_map = {'S': 'spades', 'H': 'hearts', 'D': 'diamonds', 'C': 'clubs'}
    suit = suit_map[suit_char.upper()]
    
    return Card(rank, suit)

@pytest.fixture
def game():
    """Provides a GinRummy instance for testing."""
    return GinRummy(agent_ids=[0, 1], log_events=False)

class TestGinRummyScoring:

    def test_no_melds(self, game):
        # Hand with no possible combinations
        hand = [C("2H"), C("4D"), C("6S"), C("8C"), C("QH"), C("KS")]
        assert game._get_unmatched_points(hand) == 2 + 4 + 6 + 8 + 10 + 10

    def test_simple_set(self, game):
        # Hand with one set of 7s
        hand = [C("7H"), C("7D"), C("7S"), C("2C"), C("5S")]
        # Deadwood should be 2 + 5 = 7
        assert game._get_unmatched_points(hand) == 7

    def test_simple_run(self, game):
        # Hand with one run of hearts
        hand = [C("5H"), C("6H"), C("7H"), C("AC"), C("KD")]
        # Deadwood should be 1 (Ace) + 10 (King) = 11
        assert game._get_unmatched_points(hand) == 11

    def test_four_of_a_kind_as_meld(self, game):
        # Four Kings should be melded, leaving 5 + 2 = 7 points
        hand = [C("KH"), C("KD"), C("KS"), C("KC"), C("5H"), C("2D")]
        assert game._get_unmatched_points(hand) == 7

    def test_long_run(self, game):
        # A 5-card run should be melded
        hand = [C("5S"), C("6S"), C("7S"), C("8S"), C("9S"), C("AH"), C("AD")]
        # Deadwood should be 1 + 1 = 2
        assert game._get_unmatched_points(hand) == 2

    def test_two_distinct_melds(self, game):
        # A set of Aces and a run of Diamonds
        hand = [C("AS"), C("AH"), C("AC"), C("2D"), C("3D"), C("4D"), C("9C")]
        # Deadwood is just the 9 of Clubs
        assert game._get_unmatched_points(hand) == 9
        
    def test_perfect_gin_hand(self, game):
        # A hand with 0 deadwood
        # Melds: (5H, 5D, 5S), (7C, 8C, 9C, TC)
        hand = [C("5H"), C("5D"), C("5S"), C("7C"), C("8C"), C("9C"), C("TC")]
        assert game._get_unmatched_points(hand) == 0

    def test_full_10_card_gin_hand(self, game):
        # Melds: (AH, 2H, 3H), (JD, QD, KD), (5S, 5C, 5H, 5D) -> impossible hand, let's fix
        # Melds: (AH, 2H, 3H), (JD, QD, KD), (5S, 5C, 5H, 9D)
        # Re-evaluating:
        # Melds: [AS,AC,AD], [5H,6H,7H], [TH,JH,QH,KH]
        hand = [
            C("AS"), C("AC"), C("AD"), # Set of Aces
            C("5H"), C("6H"), C("7H"), # Run of Hearts
            C("TH"), C("JH"), C("QH"), C("KH") # Run of Hearts is not possible, let's use diamonds
        ]
        hand = [
            C("AS"), C("AC"), C("AD"), 
            C("5H"), C("6H"), C("7H"),
            C("TD"), C("JD"), C("QD"), C("KD")
        ]
        assert game._get_unmatched_points(hand) == 0
        
    def test_overlapping_meld_choice_prefers_lower_deadwood(self, game):
        # Hand: [7S, 7H, 7D, 8D, 9D]. 7D is the pivot.
        # Option 1: Meld (7S, 7H, 7D). Deadwood: 8D, 9D (17 points).
        # Option 2: Meld (7D, 8D, 9D). Deadwood: 7S, 7H (14 points).
        # Solver should choose Option 2.
        hand = [C("7S"), C("7H"), C("7D"), C("8D"), C("9D")]
        assert game._get_unmatched_points(hand) == 14

    def test_four_of_a_kind_split_for_run(self, game):
        # This tests the critical fix from our discussion.
        # Hand: [7S, 7H, 7D, 7C, 8C, 9C]
        # Optimal: Meld (7S, 7H, 7D) and (7C, 8C, 9C). Deadwood = 0.
        # Wrong: Meld (7S, 7H, 7D, 7C). Deadwood: 8C, 9C (17 points).
        hand = [C("7S"), C("7H"), C("7D"), C("7C"), C("8C"), C("9C")]
        assert game._get_unmatched_points(hand) == 0

    def test_ace_low_run(self, game):
        # Ace can be used in A-2-3 run
        hand = [C("AS"), C("2S"), C("3S"), C("KD"), C("QC")]
        assert game._get_unmatched_points(hand) == 20 # King + Queen

    def test_ace_high_run_is_invalid(self, game):
        # Ace cannot be used in Q-K-A run
        hand = [C("QS"), C("KS"), C("AS")]
        # All cards should be deadwood
        assert game._get_unmatched_points(hand) == 10 + 10 + 1 # 21
        
    def test_empty_hand(self, game):
        assert game._get_unmatched_points([]) == 0
        
    def test_complex_hand_with_multiple_choices(self, game):
        # Hand: [5D, 6D, 7D, 5H, 6H, 7H, 5S, 6S, 7S]
        # Three runs for 0 points.
        hand = [C("4D"), C("5D"), C("6D"), C("5H"), C("6H"), C("7H"), C("5S"), C("6S"), C("7S")]
        assert game._get_unmatched_points(hand) == 0

        # Now add a card that could break one run to make a set
        # Hand: [4D, 5D, 6D, 5H, 6H, 7H, 5S, 6S, 7S, 5C]
        # Optimal should be: keep the three runs, deadwood is 5C (5 points).
        hand.append(C("5C"))
        assert game._get_unmatched_points(hand) == 5

class TestGinRummyGameFlow:

    def test_initial_deal(self, game):
        """Verify the game state after the initial deal."""
        game.init_game()

        # Each player should have 10 cards
        assert len(game.hands[0]) == 10
        assert len(game.hands[1]) == 10

        # Discard pile should have 1 card
        assert len(game.discard) == 1
        
        # Stock should have the remaining cards (52 - 20 - 1 = 31)
        assert len(game.stock) == 31
        
        # Game should be in the upcard draw phase
        assert game.phase == "upcard_draw"
        assert not game.done

    def test_upcard_phase_take_and_discard(self, game):
        """Test a player taking the upcard and then discarding."""
        game.init_game()
        
        # Let's say agent 0 starts
        game.current_agent = 0
        upcard = game.discard[-1]
        
        # Agent 0 takes the upcard
        game.step(Action(action_type=ActionType.TAKE_UPCARD))
        
        # Agent 0 should now have 11 cards, including the upcard
        assert len(game.hands[0]) == 11
        assert upcard in game.hands[0]
        assert len(game.discard) == 0
        assert game.phase == "upcard_discard"
        
        # Agent 0 now discards a card
        card_to_discard = game.hands[0][0]
        game.step(Action(action_type=ActionType.DISCARD, card=card_to_discard))
        
        # Agent 0 should have 10 cards, discard pile has 1
        assert len(game.hands[0]) == 10
        assert card_to_discard not in game.hands[0]
        assert len(game.discard) == 1
        assert game.discard[-1] == card_to_discard
        
        # Phase should be 'draw' and it should be agent 1's turn
        assert game.phase == "draw"
        assert game.current_agent == 1

    def test_upcard_phase_full_pass(self, game):
        """Test both players passing on the upcard."""
        game.init_game()
        starting_agent = game.current_agent
        other_agent = 1 - starting_agent
        
        # First player passes
        game.step(Action(action_type=ActionType.PASS_UPCARD))
        assert game.current_agent == other_agent
        assert game.phase == "upcard_draw"
        
        # Second player passes
        game.step(Action(action_type=ActionType.PASS_UPCARD))
        
        # Should be back to the starting player's turn, in the 'draw' phase
        assert game.current_agent == starting_agent
        assert game.phase == "draw"

    def test_draw_from_stock_and_discard(self, game):
        """Test a normal turn: drawing from stock and discarding."""
        game.init_game()
        game.phase = "draw"
        game.current_agent = 0
        stock_size = len(game.stock)
        
        # Agent 0 draws from stock
        game.step(Action(action_type=ActionType.DRAW_FROM_STOCK))
        
        assert len(game.hands[0]) == 11
        assert len(game.stock) == stock_size - 1
        assert game.phase == "discard"
        assert game.current_agent == 0
        
        # Agent 0 discards
        card_to_discard = game.hands[0][0]
        game.step(Action(action_type=ActionType.DISCARD, card=card_to_discard))

        assert len(game.hands[0]) == 10
        assert card_to_discard in game.discard
        assert game.phase == "draw"
        assert game.current_agent == 1
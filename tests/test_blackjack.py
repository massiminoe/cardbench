import unittest
from unittest.mock import MagicMock, patch

from src.games.blackjack.blackjack import Blackjack, Action, ActionType
from src.games.common import Card


class TestBlackjack(unittest.TestCase):

    def setUp(self):
        """Set up a new Blackjack game for each test."""
        self.game = Blackjack(log_events=False)
        self.game.init_game()

    def test_get_hand_value(self):
        """Test the calculation of hand values."""
        game = self.game
        # Test basic hands
        self.assertEqual(game._get_hand_value([Card("2", "H"), Card("3", "D")]), 5)
        self.assertEqual(game._get_hand_value([Card("K", "S"), Card("Q", "C")]), 20)
        # Test with Aces
        self.assertEqual(game._get_hand_value([Card("A", "H"), Card("5", "D")]), 16)
        self.assertEqual(game._get_hand_value([Card("A", "H"), Card("K", "D")]), 21)
        self.assertEqual(
            game._get_hand_value([Card("A", "H"), Card("A", "D")]), 12
        )  # A, A -> 11 + 1
        self.assertEqual(
            game._get_hand_value([Card("A", "H"), Card("A", "D"), Card("A", "C")]), 13
        )  # A, A, A -> 11 + 1 + 1
        self.assertEqual(
            game._get_hand_value([Card("A", "H"), Card("5", "D"), Card("7", "S")]), 13
        )  # A, 5, 7 -> 1 + 5 + 7
        self.assertEqual(game._get_hand_value([Card("A", "H"), Card("9", "D"), Card("A", "S")]), 21)

    def test_player_bust(self):
        """Test that the player busts correctly."""
        self.game.player_hand = [Card("K", "H"), Card("Q", "D")]  # Player has 20
        self.game.deck.deal_with_replacement = MagicMock(
            return_value=[Card("5", "C")]
        )  # Next card is a 5
        self.game.step(Action(ActionType.HIT))
        self.assertTrue(self.game.done)
        self.assertEqual(self.game.payout, -1.0)

    def test_resolve_blackjack_win(self):
        """Test the resolution logic for a player's natural blackjack win."""
        self.game.player_hand = [Card("A", "S"), Card("J", "C")]  # Player has blackjack
        self.game.dealer_hand = [Card("7", "D"), Card("8", "H")]  # Dealer has 15
        self.game._resolve_game()
        self.assertTrue(self.game.done)
        self.assertEqual(self.game.payout, 1.5)

    @patch("src.games.blackjack.blackjack.Deck")
    def test_player_blackjack_on_deal(self, MockDeck):
        """Test the full game flow for a player's natural blackjack on deal."""
        mock_deck_instance = MockDeck.return_value
        mock_deck_instance.deal_with_replacement.side_effect = [
            [Card("A", "S"), Card("J", "C")],  # Player's initial hand
            [Card("7", "D")],  # Dealer's initial hand
            [Card("T", "H")],  # Dealer's second card
        ]
        game = Blackjack(log_events=False)
        game.init_game()

        # init_game should detect blackjack and play the dealer's turn.
        self.assertTrue(game.done)
        self.assertEqual(game.payout, 1.5)  # Player blackjack vs dealer 17

    def test_dealer_turn(self):
        """Test the dealer's playing logic."""
        self.game.player_hand = [Card("K", "H"), Card("7", "D")]  # Player stands on 17
        self.game.dealer_hand = [Card("K", "S"), Card("6", "C")]  # Dealer has 16
        # Mock deck to control dealer's draw
        self.game.deck.deal_with_replacement = MagicMock(
            return_value=[Card("5", "H")]
        )  # Dealer gets 21
        self.game.step(Action(ActionType.STAND))

        self.assertEqual(self._get_hand_value(self.game.dealer_hand), 21)
        self.assertTrue(self.game.done)
        self.assertEqual(self.game.payout, -1.0)  # Player loses

    def test_push(self):
        """Test a push scenario."""
        self.game.player_hand = [Card("K", "H"), Card("9", "D")]  # Player has 19
        self.game.dealer_hand = [Card("K", "S"), Card("9", "C")]  # Dealer also has 19
        self.game._resolve_game()
        self.assertTrue(self.game.done)
        self.assertEqual(self.game.payout, 0.0)

    def _get_hand_value(self, hand):
        """Helper to call protected method for testing."""
        return self.game._get_hand_value(hand)


if __name__ == "__main__":
    unittest.main()

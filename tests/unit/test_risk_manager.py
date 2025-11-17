"""
Unit tests for RiskManager.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.trading.risk_manager import RiskManager
from src.database.models import Trade, TradeSide, TradeStatus


@pytest.mark.unit
class TestRiskManager:
    """Test RiskManager class."""

    def test_initialization(self):
        """Test risk manager initialization."""
        rm = RiskManager()

        assert rm.max_position_size > 0
        assert rm.max_daily_loss > 0
        assert rm.stop_loss_percent > 0
        assert rm.take_profit_percent > 0
        assert rm.max_concurrent_positions > 0

    def test_calculate_position_size_basic(self):
        """Test basic position size calculation."""
        rm = RiskManager()

        account_balance = 10000.0
        entry_price = 45000.0
        stop_loss = 44500.0
        confidence = 1.0

        position_size = rm.calculate_position_size(
            account_balance, entry_price, stop_loss, confidence
        )

        assert position_size > 0
        assert position_size <= account_balance * rm.max_position_size

    def test_calculate_position_size_with_confidence(self):
        """Test position sizing with different confidence levels."""
        rm = RiskManager()

        account_balance = 10000.0
        entry_price = 45000.0
        stop_loss = 44500.0

        # High confidence
        size_high = rm.calculate_position_size(
            account_balance, entry_price, stop_loss, confidence=0.9
        )

        # Low confidence
        size_low = rm.calculate_position_size(
            account_balance, entry_price, stop_loss, confidence=0.5
        )

        # Higher confidence should result in larger position
        assert size_high > size_low

    def test_calculate_position_size_zero_risk(self):
        """Test position sizing when stop loss equals entry price."""
        rm = RiskManager()

        account_balance = 10000.0
        entry_price = 45000.0
        stop_loss = 45000.0  # No risk
        confidence = 1.0

        position_size = rm.calculate_position_size(
            account_balance, entry_price, stop_loss, confidence
        )

        # Should still return a valid position size
        assert position_size > 0

    def test_calculate_stop_loss_buy_fixed(self):
        """Test stop loss calculation for BUY with fixed percentage."""
        rm = RiskManager()

        entry_price = 45000.0
        stop_loss = rm.calculate_stop_loss(entry_price, "BUY")

        # Stop loss should be below entry for BUY
        assert stop_loss < entry_price

        # Check percentage
        expected_distance = entry_price * rm.stop_loss_percent
        assert abs((entry_price - stop_loss) - expected_distance) < 0.01

    def test_calculate_stop_loss_sell_fixed(self):
        """Test stop loss calculation for SELL with fixed percentage."""
        rm = RiskManager()

        entry_price = 45000.0
        stop_loss = rm.calculate_stop_loss(entry_price, "SELL")

        # Stop loss should be above entry for SELL
        assert stop_loss > entry_price

    def test_calculate_stop_loss_with_atr(self):
        """Test dynamic stop loss using ATR."""
        rm = RiskManager()

        entry_price = 45000.0
        atr = 300.0

        stop_loss = rm.calculate_stop_loss(entry_price, "BUY", atr=atr)

        # Should use ATR-based distance
        expected_distance = atr * 1.5
        assert abs((entry_price - stop_loss) - expected_distance) < 0.01

    def test_calculate_take_profit_buy(self):
        """Test take profit calculation for BUY."""
        rm = RiskManager()

        entry_price = 45000.0
        take_profit = rm.calculate_take_profit(entry_price, "BUY")

        # Take profit should be above entry for BUY
        assert take_profit > entry_price

    def test_calculate_take_profit_sell(self):
        """Test take profit calculation for SELL."""
        rm = RiskManager()

        entry_price = 45000.0
        take_profit = rm.calculate_take_profit(entry_price, "SELL")

        # Take profit should be below entry for SELL
        assert take_profit < entry_price

    def test_calculate_take_profit_risk_reward_ratio(self):
        """Test take profit with different risk/reward ratios."""
        rm = RiskManager()

        entry_price = 45000.0

        tp_2x = rm.calculate_take_profit(entry_price, "BUY", risk_reward_ratio=2.0)
        tp_3x = rm.calculate_take_profit(entry_price, "BUY", risk_reward_ratio=3.0)

        # Higher risk/reward should have higher take profit
        assert tp_3x > tp_2x

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_can_open_position_success(self, mock_trade_repo, mock_db):
        """Test can open position when all checks pass."""
        rm = RiskManager()

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        # No open trades
        mock_trade_repo.get_open_trades.return_value = []
        mock_trade_repo.get_performance_summary.return_value = {'total_pnl': 100.0}

        can_trade, reason = rm.can_open_position("BTC/USDT", account_balance=10000)

        assert can_trade is True
        assert reason == "OK"

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_can_open_position_max_positions_reached(self, mock_trade_repo, mock_db):
        """Test cannot open position when max concurrent positions reached."""
        rm = RiskManager()

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        # Create max number of open trades
        mock_trades = [MagicMock(symbol=f"SYMBOL{i}") for i in range(rm.max_concurrent_positions)]
        mock_trade_repo.get_open_trades.return_value = mock_trades

        can_trade, reason = rm.can_open_position("BTC/USDT", account_balance=10000)

        assert can_trade is False
        assert "Max concurrent positions" in reason

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_can_open_position_duplicate_symbol(self, mock_trade_repo, mock_db):
        """Test cannot open position if already have position in same symbol."""
        rm = RiskManager()

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        # Already have position in BTC/USDT
        mock_trade = MagicMock(symbol="BTC/USDT")
        mock_trade_repo.get_open_trades.return_value = [mock_trade]

        can_trade, reason = rm.can_open_position("BTC/USDT", account_balance=10000)

        assert can_trade is False
        assert "Already have open position" in reason

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_can_open_position_daily_loss_limit(self, mock_trade_repo, mock_db):
        """Test cannot open position when daily loss limit reached."""
        rm = RiskManager()

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        mock_trade_repo.get_open_trades.return_value = []

        # Simulate daily loss exceeding limit
        account_balance = 10000.0
        daily_loss = -1000.0  # -10% loss
        mock_trade_repo.get_performance_summary.return_value = {'total_pnl': daily_loss}

        can_trade, reason = rm.can_open_position("BTC/USDT", account_balance=account_balance)

        assert can_trade is False
        assert "Daily loss limit" in reason

    def test_should_close_position_buy_stop_loss(self):
        """Test should close BUY position when stop loss hit."""
        rm = RiskManager()

        current_price = 44000.0  # Below stop loss
        entry_price = 45000.0
        stop_loss = 44500.0
        take_profit = 46000.0

        should_close, reason = rm.should_close_position(
            current_price, entry_price, stop_loss, take_profit, "BUY"
        )

        assert should_close is True
        assert reason == "Stop Loss"

    def test_should_close_position_buy_take_profit(self):
        """Test should close BUY position when take profit hit."""
        rm = RiskManager()

        current_price = 46100.0  # Above take profit
        entry_price = 45000.0
        stop_loss = 44500.0
        take_profit = 46000.0

        should_close, reason = rm.should_close_position(
            current_price, entry_price, stop_loss, take_profit, "BUY"
        )

        assert should_close is True
        assert reason == "Take Profit"

    def test_should_close_position_buy_no_close(self):
        """Test should NOT close BUY position when price in range."""
        rm = RiskManager()

        current_price = 45500.0  # Between stop loss and take profit
        entry_price = 45000.0
        stop_loss = 44500.0
        take_profit = 46000.0

        should_close, reason = rm.should_close_position(
            current_price, entry_price, stop_loss, take_profit, "BUY"
        )

        assert should_close is False
        assert reason == ""

    def test_should_close_position_sell_stop_loss(self):
        """Test should close SELL position when stop loss hit."""
        rm = RiskManager()

        current_price = 46000.0  # Above stop loss
        entry_price = 45000.0
        stop_loss = 45500.0
        take_profit = 44000.0

        should_close, reason = rm.should_close_position(
            current_price, entry_price, stop_loss, take_profit, "SELL"
        )

        assert should_close is True
        assert reason == "Stop Loss"

    def test_should_close_position_sell_take_profit(self):
        """Test should close SELL position when take profit hit."""
        rm = RiskManager()

        current_price = 43900.0  # Below take profit
        entry_price = 45000.0
        stop_loss = 45500.0
        take_profit = 44000.0

        should_close, reason = rm.should_close_position(
            current_price, entry_price, stop_loss, take_profit, "SELL"
        )

        assert should_close is True
        assert reason == "Take Profit"

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_get_risk_metrics(self, mock_trade_repo, mock_db):
        """Test getting risk metrics."""
        rm = RiskManager()

        mock_session = MagicMock()

        mock_trade_repo.get_open_trades.return_value = [MagicMock(), MagicMock()]
        mock_trade_repo.get_performance_summary.return_value = {
            'total_trades': 50,
            'win_rate': 0.60,
            'total_pnl': 500.0,
            'avg_pnl': 10.0
        }

        metrics = rm.get_risk_metrics(mock_session)

        assert metrics['open_positions'] == 2
        assert metrics['total_trades_30d'] == 50
        assert metrics['win_rate_30d'] == 0.60
        assert metrics['total_pnl_30d'] == 500.0

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_calculate_kelly_criterion(self, mock_trade_repo, mock_db):
        """Test Kelly Criterion calculation."""
        rm = RiskManager()

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        mock_trade_repo.get_performance_summary.return_value = {
            'win_rate': 0.60,
            'largest_win': 100.0,
            'largest_loss': -50.0
        }

        kelly = rm._calculate_kelly_criterion()

        # Kelly should be between 1% and 10% (capped)
        assert 0.01 <= kelly <= 0.10

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_calculate_kelly_criterion_no_losses(self, mock_trade_repo, mock_db):
        """Test Kelly Criterion when no losses (edge case)."""
        rm = RiskManager()

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        mock_trade_repo.get_performance_summary.return_value = {
            'win_rate': 1.0,
            'largest_win': 100.0,
            'largest_loss': 0.0  # No losses
        }

        kelly = rm._calculate_kelly_criterion()

        # Should return default 2%
        assert kelly == 0.02

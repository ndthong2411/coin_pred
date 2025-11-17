"""
Unit tests for TradingExecutor.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.trading.executor import TradingExecutor
from src.database.models import Trade, TradeSide, OrderType, TradeStatus


@pytest.mark.unit
class TestTradingExecutor:
    """Test TradingExecutor class."""

    def test_initialization_paper_mode(self):
        """Test executor initialization in paper mode."""
        executor = TradingExecutor(mode="paper")

        assert executor.mode == "paper"
        assert executor.is_live is False

    def test_initialization_live_mode(self):
        """Test executor initialization in live mode."""
        executor = TradingExecutor(mode="live")

        assert executor.mode == "live"
        assert executor.is_live is True

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.telegram')
    def test_execute_signal_hold_action(
        self, mock_telegram, mock_db, mock_binance, mock_risk_manager, sample_signal
    ):
        """Test that HOLD signal returns None."""
        executor = TradingExecutor(mode="paper")

        signal = sample_signal.copy()
        signal['action'] = 'HOLD'

        trade = executor.execute_signal("BTC/USDT", signal, account_balance=10000)

        assert trade is None

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.telegram')
    def test_execute_signal_cannot_open_position(
        self, mock_telegram, mock_db, mock_binance, mock_risk_manager, sample_signal
    ):
        """Test signal execution when position cannot be opened."""
        executor = TradingExecutor(mode="paper")

        # Mock risk manager to deny trade
        mock_risk_manager.can_open_position.return_value = (False, "Max positions reached")

        trade = executor.execute_signal("BTC/USDT", sample_signal, account_balance=10000)

        assert trade is None
        mock_risk_manager.can_open_position.assert_called_once()

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.telegram')
    @patch('src.trading.executor.TradeRepository')
    def test_execute_paper_trade_buy(
        self, mock_trade_repo, mock_telegram, mock_db, mock_binance, mock_risk_manager, sample_signal
    ):
        """Test paper trade execution for BUY signal."""
        executor = TradingExecutor(mode="paper")

        # Setup mocks
        mock_risk_manager.can_open_position.return_value = (True, "OK")
        mock_risk_manager.calculate_stop_loss.return_value = 44500.0
        mock_risk_manager.calculate_position_size.return_value = 450.0
        mock_risk_manager.calculate_take_profit.return_value = 46000.0
        mock_binance.get_price.return_value = 45000.0

        # Mock database session
        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        # Mock created trade
        mock_trade = Mock(spec=Trade)
        mock_trade.id = 1
        mock_trade_repo.create.return_value = mock_trade

        trade = executor.execute_signal("BTC/USDT", sample_signal, account_balance=10000)

        # Assertions
        assert trade == mock_trade
        mock_risk_manager.can_open_position.assert_called_once()
        mock_risk_manager.calculate_position_size.assert_called_once()
        mock_trade_repo.create.assert_called_once()
        mock_telegram.send_trade_execution.assert_called_once()

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.telegram')
    @patch('src.trading.executor.TradeRepository')
    def test_execute_live_trade_success(
        self, mock_trade_repo, mock_telegram, mock_db, mock_binance, mock_risk_manager, sample_signal
    ):
        """Test live trade execution success."""
        executor = TradingExecutor(mode="live")

        # Setup mocks
        mock_risk_manager.can_open_position.return_value = (True, "OK")
        mock_risk_manager.calculate_stop_loss.return_value = 44500.0
        mock_risk_manager.calculate_position_size.return_value = 450.0
        mock_risk_manager.calculate_take_profit.return_value = 46000.0

        mock_binance.create_market_order.return_value = {
            'orderId': 12345,
            'status': 'FILLED',
            'executedQty': '0.01',
            'fills': [{'price': '45000.0'}]
        }
        mock_binance.create_oco_order.return_value = {
            'orderListId': 67890
        }

        # Mock database
        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        mock_trade = Mock(spec=Trade)
        mock_trade_repo.create.return_value = mock_trade

        trade = executor.execute_signal("BTC/USDT", sample_signal, account_balance=10000)

        # Assertions
        assert trade == mock_trade
        mock_binance.create_market_order.assert_called_once()
        mock_binance.create_oco_order.assert_called_once()
        mock_trade_repo.create.assert_called_once()

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.telegram')
    def test_execute_live_trade_failure(
        self, mock_telegram, mock_binance, mock_risk_manager, sample_signal
    ):
        """Test live trade execution failure."""
        executor = TradingExecutor(mode="live")

        # Setup mocks
        mock_risk_manager.can_open_position.return_value = (True, "OK")
        mock_risk_manager.calculate_stop_loss.return_value = 44500.0
        mock_risk_manager.calculate_position_size.return_value = 450.0
        mock_risk_manager.calculate_take_profit.return_value = 46000.0

        # Simulate API error
        mock_binance.create_market_order.side_effect = Exception("API Error")

        trade = executor.execute_signal("BTC/USDT", sample_signal, account_balance=10000)

        # Should return None on failure
        assert trade is None
        mock_telegram.send_error.assert_called_once()

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.TradeRepository')
    def test_check_and_close_positions(
        self, mock_trade_repo, mock_db, mock_binance, mock_risk_manager
    ):
        """Test checking and closing positions."""
        executor = TradingExecutor(mode="paper")

        # Mock open trades
        mock_trade = Mock(spec=Trade)
        mock_trade.id = 1
        mock_trade.symbol = "BTC/USDT"
        mock_trade.entry_price = 45000.0
        mock_trade.stop_loss = 44500.0
        mock_trade.take_profit = 46000.0
        mock_trade.side = TradeSide.BUY

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session
        mock_trade_repo.get_open_trades.return_value = [mock_trade]

        mock_binance.get_price.return_value = 46100.0  # Above take profit
        mock_risk_manager.should_close_position.return_value = (True, "Take Profit")

        executor.check_and_close_positions()

        # Verify methods called
        mock_trade_repo.get_open_trades.assert_called_once()
        mock_binance.get_price.assert_called_once()
        mock_risk_manager.should_close_position.assert_called_once()

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.TradeRepository')
    @patch('src.trading.executor.telegram')
    def test_close_position_paper_mode(
        self, mock_telegram, mock_trade_repo, mock_db, mock_binance, mock_risk_manager, sample_trade
    ):
        """Test closing position in paper mode."""
        executor = TradingExecutor(mode="paper")

        mock_session = MagicMock()

        executor.close_position(sample_trade, exit_price=46000.0, reason="Take Profit", session=mock_session)

        # Verify trade closed
        mock_trade_repo.close_trade.assert_called_once_with(mock_session, sample_trade.id, 46000.0)
        sample_trade.calculate_profit_loss.assert_called_once()
        mock_telegram.send_trade_closed.assert_called_once()

    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.TradeRepository')
    @patch('src.trading.executor.telegram')
    def test_close_position_live_mode(
        self, mock_telegram, mock_trade_repo, mock_db, mock_binance, mock_risk_manager, sample_trade
    ):
        """Test closing position in live mode."""
        executor = TradingExecutor(mode="live")

        mock_session = MagicMock()

        # Mock Binance order
        mock_binance.create_market_order.return_value = {
            'orderId': 99999,
            'fills': [{'price': '46000.0'}]
        }

        sample_trade.stop_loss_order_id = "123456"

        executor.close_position(sample_trade, exit_price=46000.0, reason="Take Profit", session=mock_session)

        # Verify order placed
        mock_binance.create_market_order.assert_called_once()
        mock_binance.cancel_order.assert_called_once()
        mock_trade_repo.close_trade.assert_called_once()

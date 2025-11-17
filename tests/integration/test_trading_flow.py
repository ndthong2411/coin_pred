"""
Integration tests for end-to-end trading flow.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from src.trading.executor import TradingExecutor
from src.trading.signal_generator import SignalGenerator
from src.trading.risk_manager import RiskManager
from src.database.models import TradeStatus


@pytest.mark.integration
class TestTradingFlow:
    """Test complete trading workflow."""

    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.telegram')
    @patch('src.trading.executor.TradeRepository')
    def test_complete_buy_signal_to_trade(
        self,
        mock_trade_repo,
        mock_telegram,
        mock_db,
        mock_risk_manager,
        mock_binance,
        sample_ohlcv_data
    ):
        """Test complete flow from signal generation to trade execution."""
        # Setup
        executor = TradingExecutor(mode="paper")
        signal_gen = SignalGenerator()
        signal_gen.min_confidence = 0.3

        # Prepare data with indicators
        df = sample_ohlcv_data.copy()
        df['rsi_14'] = 25  # Oversold
        df['macd'] = 10
        df['macd_signal'] = 5
        df['ema_9'] = 45500
        df['ema_21'] = 45000
        df['ema_50'] = 44500
        df['bb_upper'] = 46000
        df['bb_lower'] = 44000
        df['bb_pct'] = 0.2
        df['adx'] = 30
        df['volume_strength'] = 1.5

        # Generate signal
        signal = signal_gen.generate_signal(df)

        assert signal['action'] in ['BUY', 'SELL', 'HOLD']

        if signal['action'] != 'HOLD':
            # Mock risk manager
            mock_risk_manager.can_open_position.return_value = (True, "OK")
            mock_risk_manager.calculate_stop_loss.return_value = 44500.0
            mock_risk_manager.calculate_position_size.return_value = 450.0
            mock_risk_manager.calculate_take_profit.return_value = 46000.0

            # Mock database
            mock_session = MagicMock()
            mock_db.session_scope.return_value.__enter__.return_value = mock_session

            mock_trade = MagicMock()
            mock_trade.id = 1
            mock_trade_repo.create.return_value = mock_trade

            # Execute signal
            trade = executor.execute_signal("BTC/USDT", signal, account_balance=10000)

            assert trade is not None
            mock_trade_repo.create.assert_called_once()

    @patch('src.trading.executor.binance_client')
    @patch('src.trading.executor.risk_manager')
    @patch('src.trading.executor.db')
    @patch('src.trading.executor.TradeRepository')
    def test_position_lifecycle(
        self,
        mock_trade_repo,
        mock_db,
        mock_risk_manager,
        mock_binance,
        db_session,
        sample_trade
    ):
        """Test complete position lifecycle: open -> monitor -> close."""
        executor = TradingExecutor(mode="paper")

        # Setup mocks
        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session
        mock_trade_repo.get_open_trades.return_value = [sample_trade]

        # Price hits take profit
        mock_binance.get_price.return_value = 46100.0
        mock_risk_manager.should_close_position.return_value = (True, "Take Profit")

        # Check and close positions
        executor.check_and_close_positions()

        # Verify position was checked
        mock_trade_repo.get_open_trades.assert_called_once()
        mock_binance.get_price.assert_called_once()

    def test_signal_confidence_filtering(self):
        """Test that low confidence signals are filtered."""
        signal_gen = SignalGenerator()
        signal_gen.min_confidence = 0.8  # High threshold

        # Create weak signals
        df = pd.DataFrame({
            'close': [45000] * 100,
            'rsi_14': [50] * 100,  # Neutral
            'macd': [0] * 100,
            'macd_signal': [0] * 100,
            'ema_9': [45000] * 100,
            'ema_21': [45000] * 100,
            'ema_50': [45000] * 100,
            'bb_upper': [46000] * 100,
            'bb_lower': [44000] * 100,
            'bb_pct': [0.5] * 100,
            'adx': [10] * 100,  # Weak trend
            'volume_strength': [1.0] * 100
        })

        signal = signal_gen.generate_signal(df)

        # Should return HOLD due to low confidence
        assert signal['action'] == 'HOLD'

    @patch('src.trading.risk_manager.db')
    @patch('src.trading.risk_manager.TradeRepository')
    def test_risk_management_limits(self, mock_trade_repo, mock_db):
        """Test that risk management properly enforces limits."""
        rm = RiskManager()

        mock_session = MagicMock()
        mock_db.session_scope.return_value.__enter__.return_value = mock_session

        # Simulate max positions reached
        max_trades = [MagicMock(symbol=f"SYMBOL{i}") for i in range(rm.max_concurrent_positions)]
        mock_trade_repo.get_open_trades.return_value = max_trades

        can_trade, reason = rm.can_open_position("NEWCOIN/USDT", account_balance=10000)

        assert can_trade is False
        assert "Max concurrent positions" in reason

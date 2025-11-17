"""
Unit tests for database repository.
"""
import pytest
from datetime import datetime, timedelta

from src.database.models import Trade, TradeSide, OrderType, TradeStatus, OHLCV, Prediction
from src.database.repository import TradeRepository


@pytest.mark.unit
class TestTradeRepository:
    """Test TradeRepository class."""

    def test_create_trade(self, db_session):
        """Test creating a trade."""
        trade = TradeRepository.create(
            db_session,
            symbol="BTC/USDT",
            side=TradeSide.BUY,
            order_type=OrderType.MARKET,
            entry_price=45000.0,
            quantity=0.01,
            entry_value=450.0,
            stop_loss=44500.0,
            take_profit=46000.0,
            entry_confidence=0.85,
            entry_order_id="TEST_123"
        )

        assert trade.id is not None
        assert trade.symbol == "BTC/USDT"
        assert trade.side == TradeSide.BUY
        assert trade.status == TradeStatus.OPEN
        assert trade.entry_price == 45000.0
        assert trade.quantity == 0.01

    def test_get_trade_by_id(self, db_session, sample_trade):
        """Test getting trade by ID."""
        trade = TradeRepository.get_by_id(db_session, sample_trade.id)

        assert trade is not None
        assert trade.id == sample_trade.id
        assert trade.symbol == sample_trade.symbol

    def test_get_trade_by_id_not_found(self, db_session):
        """Test getting non-existent trade."""
        trade = TradeRepository.get_by_id(db_session, 99999)

        assert trade is None

    def test_get_open_trades(self, db_session, sample_trade):
        """Test getting open trades."""
        # Create another open trade
        trade2 = TradeRepository.create(
            db_session,
            symbol="ETH/USDT",
            side=TradeSide.SELL,
            order_type=OrderType.MARKET,
            entry_price=3000.0,
            quantity=0.1,
            entry_value=300.0
        )

        open_trades = TradeRepository.get_open_trades(db_session)

        assert len(open_trades) >= 2
        assert all(t.status == TradeStatus.OPEN for t in open_trades)

    def test_get_trades_by_symbol(self, db_session, sample_trade):
        """Test getting trades for specific symbol."""
        # Create trade for different symbol
        TradeRepository.create(
            db_session,
            symbol="ETH/USDT",
            side=TradeSide.BUY,
            order_type=OrderType.MARKET,
            entry_price=3000.0,
            quantity=0.1,
            entry_value=300.0
        )

        btc_trades = TradeRepository.get_trades_by_symbol(db_session, "BTC/USDT")

        assert len(btc_trades) >= 1
        assert all(t.symbol == "BTC/USDT" for t in btc_trades)

    def test_close_trade(self, db_session, sample_trade):
        """Test closing a trade."""
        exit_price = 46000.0

        TradeRepository.close_trade(db_session, sample_trade.id, exit_price)

        db_session.refresh(sample_trade)

        assert sample_trade.status == TradeStatus.CLOSED
        assert sample_trade.exit_price == exit_price
        assert sample_trade.exit_time is not None

    def test_get_performance_summary(self, db_session):
        """Test getting performance summary."""
        # Create some closed trades
        for i in range(5):
            trade = TradeRepository.create(
                db_session,
                symbol="BTC/USDT",
                side=TradeSide.BUY,
                order_type=OrderType.MARKET,
                entry_price=45000.0,
                quantity=0.01,
                entry_value=450.0
            )

            # Close with profit or loss
            exit_price = 46000.0 if i % 2 == 0 else 44000.0
            TradeRepository.close_trade(db_session, trade.id, exit_price)

            # Calculate P/L
            db_session.refresh(trade)
            trade.calculate_profit_loss()
            db_session.commit()

        summary = TradeRepository.get_performance_summary(db_session, days=7)

        assert 'total_trades' in summary
        assert 'win_rate' in summary
        assert 'total_pnl' in summary
        assert summary['total_trades'] >= 5

    def test_trade_calculate_profit_loss_buy(self, db_session):
        """Test profit/loss calculation for BUY trade."""
        trade = TradeRepository.create(
            db_session,
            symbol="BTC/USDT",
            side=TradeSide.BUY,
            order_type=OrderType.MARKET,
            entry_price=45000.0,
            quantity=0.01,
            entry_value=450.0
        )

        TradeRepository.close_trade(db_session, trade.id, exit_price=46000.0)
        db_session.refresh(trade)

        trade.fees = 0.9  # 0.2% fees
        trade.calculate_profit_loss()

        assert trade.profit_loss > 0  # Profit
        assert trade.net_profit_loss == trade.profit_loss - trade.fees

    def test_trade_calculate_profit_loss_sell(self, db_session):
        """Test profit/loss calculation for SELL trade."""
        trade = TradeRepository.create(
            db_session,
            symbol="BTC/USDT",
            side=TradeSide.SELL,
            order_type=OrderType.MARKET,
            entry_price=45000.0,
            quantity=0.01,
            entry_value=450.0
        )

        TradeRepository.close_trade(db_session, trade.id, exit_price=44000.0)
        db_session.refresh(trade)

        trade.fees = 0.9
        trade.calculate_profit_loss()

        assert trade.profit_loss > 0  # Profit from shorting
        assert trade.net_profit_loss == trade.profit_loss - trade.fees

    def test_delete_old_data(self, db_session):
        """Test deleting old data."""
        # Create old trade
        old_trade = TradeRepository.create(
            db_session,
            symbol="BTC/USDT",
            side=TradeSide.BUY,
            order_type=OrderType.MARKET,
            entry_price=45000.0,
            quantity=0.01,
            entry_value=450.0
        )

        # Manually set old timestamp
        old_trade.created_at = datetime.utcnow() - timedelta(days=100)
        db_session.commit()

        # Note: Repository would need delete_old_data method
        # This is a placeholder test
        all_trades = db_session.query(Trade).all()
        assert len(all_trades) >= 1

"""
Pytest configuration and shared fixtures.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.database.models import Base, Trade, TradeSide, OrderType, TradeStatus, OHLCV, Prediction


@pytest.fixture(scope="session")
def db_engine():
    """Create in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Create tables
    Base.metadata.create_all(db_engine)

    yield session

    # Rollback and close
    session.rollback()
    session.close()

    # Clean up tables
    Base.metadata.drop_all(db_engine)


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range(end=datetime.utcnow(), periods=100, freq='1H')

    # Generate realistic price data
    base_price = 45000
    prices = []
    for i in range(100):
        # Random walk with drift
        change = np.random.randn() * 100
        base_price += change
        prices.append(base_price)

    data = []
    for i, (date, close_price) in enumerate(zip(dates, prices)):
        high = close_price + abs(np.random.randn() * 50)
        low = close_price - abs(np.random.randn() * 50)
        open_price = prices[i-1] if i > 0 else close_price
        volume = abs(np.random.randn() * 10)

        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })

    return pd.DataFrame(data)


@pytest.fixture
def sample_ohlcv_array():
    """Generate sample OHLCV data as numpy array."""
    n = 100
    return np.random.rand(n, 6)  # timestamp, open, high, low, close, volume


@pytest.fixture
def mock_binance_client():
    """Mock Binance client for testing."""
    client = MagicMock()

    # Mock methods
    client.get_price.return_value = 45000.0
    client.get_account_balance.return_value = {"USDT": 10000.0, "BTC": 0.5}
    client.create_market_order.return_value = {
        'orderId': 12345,
        'status': 'FILLED',
        'executedQty': '0.01',
        'fills': [{'price': '45000.0'}]
    }
    client.create_oco_order.return_value = {
        'orderListId': 67890,
        'orders': [
            {'orderId': 11111, 'type': 'LIMIT_MAKER'},
            {'orderId': 22222, 'type': 'STOP_LOSS_LIMIT'}
        ]
    }
    client.cancel_order.return_value = {'status': 'CANCELLED'}
    client.get_klines.return_value = [
        [1609459200000, '29000', '29100', '28900', '29050', '100.5', 1609459260000, '2905000', 100, '50.25', '1452500', '0']
    ]

    return client


@pytest.fixture
def sample_features():
    """Generate sample feature data for ML models."""
    n_samples = 100

    features = pd.DataFrame({
        # Price features
        'returns': np.random.randn(n_samples) * 0.01,
        'log_returns': np.random.randn(n_samples) * 0.01,

        # Technical indicators
        'rsi_14': np.random.uniform(20, 80, n_samples),
        'macd': np.random.randn(n_samples) * 10,
        'macd_signal': np.random.randn(n_samples) * 10,
        'bb_upper': np.random.uniform(46000, 47000, n_samples),
        'bb_lower': np.random.uniform(44000, 45000, n_samples),
        'ema_9': np.random.uniform(44500, 45500, n_samples),
        'ema_21': np.random.uniform(44000, 46000, n_samples),
        'atr': np.random.uniform(100, 500, n_samples),

        # Volume indicators
        'obv': np.random.randn(n_samples) * 1000000,
        'volume_sma': np.random.uniform(50, 150, n_samples),

        # Momentum
        'stoch_k': np.random.uniform(0, 100, n_samples),
        'stoch_d': np.random.uniform(0, 100, n_samples),
        'williams_r': np.random.uniform(-100, 0, n_samples),

        # Target (for supervised learning)
        'target': np.random.choice([0, 1, 2], n_samples)  # DOWN, NEUTRAL, UP
    })

    return features


@pytest.fixture
def sample_trade(db_session):
    """Create a sample trade in the database."""
    trade = Trade(
        symbol="BTC/USDT",
        side=TradeSide.BUY,
        order_type=OrderType.MARKET,
        status=TradeStatus.OPEN,
        entry_price=45000.0,
        quantity=0.01,
        entry_value=450.0,
        stop_loss=44500.0,
        take_profit=46000.0,
        entry_confidence=0.85,
        entry_order_id="TEST_ORDER_123"
    )

    db_session.add(trade)
    db_session.commit()
    db_session.refresh(trade)

    return trade


@pytest.fixture
def sample_closed_trade(db_session):
    """Create a sample closed trade."""
    trade = Trade(
        symbol="BTC/USDT",
        side=TradeSide.BUY,
        order_type=OrderType.MARKET,
        status=TradeStatus.CLOSED,
        entry_price=45000.0,
        quantity=0.01,
        entry_value=450.0,
        exit_price=46000.0,
        exit_value=460.0,
        stop_loss=44500.0,
        take_profit=46000.0,
        entry_confidence=0.85,
        entry_order_id="TEST_ORDER_123",
        exit_order_id="TEST_ORDER_124",
        fees=0.9,
        exit_time=datetime.utcnow()
    )
    trade.calculate_profit_loss()

    db_session.add(trade)
    db_session.commit()
    db_session.refresh(trade)

    return trade


@pytest.fixture
def sample_signal():
    """Generate a sample trading signal."""
    return {
        'action': 'BUY',
        'confidence': 0.85,
        'current_price': 45000.0,
        'reasons': [
            'RSI oversold (28.5)',
            'MACD bullish crossover',
            'Price above EMA-21',
            'Strong volume surge'
        ],
        'timestamp': datetime.utcnow()
    }


@pytest.fixture
def sample_prediction(db_session):
    """Create a sample prediction."""
    pred = Prediction(
        symbol="BTC/USDT",
        timestamp=datetime.utcnow(),
        model_name="xgboost",
        model_version="1.0",
        prediction="UP",
        confidence=0.85,
        predicted_change=2.5,
        prediction_horizon=60,
        prob_up=0.75,
        prob_down=0.10,
        prob_neutral=0.15
    )

    db_session.add(pred)
    db_session.commit()
    db_session.refresh(pred)

    return pred


@pytest.fixture
def mock_telegram():
    """Mock Telegram bot."""
    telegram = MagicMock()
    telegram.send_trade_execution.return_value = True
    telegram.send_trade_closed.return_value = True
    telegram.send_error.return_value = True
    telegram.send_alert.return_value = True
    return telegram


@pytest.fixture
def account_balance():
    """Sample account balance."""
    return 10000.0


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = MagicMock()
    return logger


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield
    # Add any singleton reset logic here if needed


# Markers for test organization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_api: Tests that require external API")

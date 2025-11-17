"""
Database models using SQLAlchemy ORM.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class TradeStatus(enum.Enum):
    """Trade status enumeration."""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TradeSide(enum.Enum):
    """Trade side enumeration."""

    BUY = "buy"
    SELL = "sell"


class OrderType(enum.Enum):
    """Order type enumeration."""

    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OHLCV(Base):
    """OHLCV candlestick data."""

    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, etc.
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_symbol_timeframe_timestamp", "symbol", "timeframe", "timestamp", unique=True),
    )

    def __repr__(self):
        return f"<OHLCV {self.symbol} {self.timeframe} {self.timestamp}>"


class SentimentData(Base):
    """Sentiment analysis data."""

    __tablename__ = "sentiment_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # twitter, reddit, news
    timestamp = Column(DateTime, nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)  # -1 to +1
    confidence = Column(Float, nullable=True)  # 0 to 1
    volume = Column(Integer, nullable=True)  # Number of mentions
    raw_data = Column(Text, nullable=True)  # JSON string with raw data
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_symbol_timestamp", "symbol", "timestamp"),)

    def __repr__(self):
        return f"<Sentiment {self.symbol} {self.source} {self.sentiment_score:.2f}>"


class Feature(Base):
    """Engineered features for ML models."""

    __tablename__ = "features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)

    # Technical indicators (sample - add more as needed)
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    ema_9 = Column(Float, nullable=True)
    ema_21 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    obv = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)

    # Sentiment
    sentiment_score = Column(Float, nullable=True)

    # Market correlation
    btc_correlation = Column(Float, nullable=True)
    market_correlation = Column(Float, nullable=True)

    # Additional features stored as JSON
    extra_features = Column(Text, nullable=True)  # JSON string

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_symbol_timeframe_timestamp", "symbol", "timeframe", "timestamp"),)

    def __repr__(self):
        return f"<Feature {self.symbol} {self.timestamp}>"


class Prediction(Base):
    """Model predictions."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    model_name = Column(String(50), nullable=False)  # xgboost, lstm, ensemble, etc.
    model_version = Column(String(20), nullable=True)

    # Prediction
    prediction = Column(String(10), nullable=False)  # UP, DOWN, NEUTRAL
    confidence = Column(Float, nullable=False)  # 0 to 1
    predicted_change = Column(Float, nullable=True)  # Predicted percentage change
    prediction_horizon = Column(Integer, nullable=False)  # Minutes ahead

    # Probabilities
    prob_up = Column(Float, nullable=True)
    prob_down = Column(Float, nullable=True)
    prob_neutral = Column(Float, nullable=True)

    # Metadata
    features_used = Column(Text, nullable=True)  # JSON array of feature names
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Prediction {self.symbol} {self.model_name} {self.prediction} ({self.confidence:.2%})>"


class Trade(Base):
    """Trading records."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(TradeSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    status = Column(SQLEnum(TradeStatus), nullable=False, default=TradeStatus.OPEN)

    # Entry
    entry_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    entry_value = Column(Float, nullable=False)  # entry_price * quantity

    # Exit
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_value = Column(Float, nullable=True)

    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    # Results
    profit_loss = Column(Float, nullable=True)  # Absolute P/L
    profit_loss_percent = Column(Float, nullable=True)  # Percentage P/L
    fees = Column(Float, nullable=False, default=0.0)
    net_profit_loss = Column(Float, nullable=True)  # P/L after fees

    # Prediction info
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    prediction = relationship("Prediction")
    entry_confidence = Column(Float, nullable=True)

    # Binance order IDs
    entry_order_id = Column(String(100), nullable=True)
    exit_order_id = Column(String(100), nullable=True)
    stop_loss_order_id = Column(String(100), nullable=True)
    take_profit_order_id = Column(String(100), nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_symbol_status", "symbol", "status"),)

    def __repr__(self):
        return f"<Trade {self.id} {self.symbol} {self.side.value} {self.status.value}>"

    def calculate_profit_loss(self):
        """Calculate profit/loss for the trade."""
        if self.exit_price is None:
            return None

        if self.side == TradeSide.BUY:
            self.profit_loss = (self.exit_price - self.entry_price) * self.quantity
        else:  # SELL (short)
            self.profit_loss = (self.entry_price - self.exit_price) * self.quantity

        self.exit_value = self.exit_price * self.quantity
        self.profit_loss_percent = self.profit_loss / self.entry_value
        self.net_profit_loss = self.profit_loss - self.fees


class PerformanceMetrics(Base):
    """Daily performance metrics."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)

    # Trading metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)

    # Financial metrics
    total_profit_loss = Column(Float, default=0.0)
    total_fees = Column(Float, default=0.0)
    net_profit_loss = Column(Float, default=0.0)
    daily_return = Column(Float, default=0.0)

    # Portfolio
    starting_balance = Column(Float, nullable=True)
    ending_balance = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)

    # Risk metrics
    sharpe_ratio = Column(Float, nullable=True)
    max_consecutive_losses = Column(Integer, default=0)
    largest_loss = Column(Float, nullable=True)
    largest_win = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Metrics {self.date.date()} Win Rate: {self.win_rate:.2%}>"


class SystemLog(Base):
    """System logs and events."""

    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    module = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    extra_data = Column(Text, nullable=True)  # JSON string

    __table_args__ = (Index("idx_timestamp_level", "timestamp", "level"),)

    def __repr__(self):
        return f"<Log {self.level} {self.timestamp}>"


if __name__ == "__main__":
    # Test models
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create in-memory database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test data
    ohlcv = OHLCV(
        symbol="BTC/USDT",
        timeframe="1m",
        timestamp=datetime.utcnow(),
        open=45000,
        high=45100,
        low=44900,
        close=45050,
        volume=100.5,
    )

    trade = Trade(
        symbol="BTC/USDT",
        side=TradeSide.BUY,
        order_type=OrderType.MARKET,
        entry_price=45000,
        quantity=0.01,
        entry_value=450,
        stop_loss=44500,
        take_profit=46000,
    )

    session.add(ohlcv)
    session.add(trade)
    session.commit()

    print("✅ Database models test complete")
    print(f"OHLCV: {ohlcv}")
    print(f"Trade: {trade}")

# 4. Core Components

## Overview

This document explains each major component in detail, including:
- What it does
- How it works
- API/interface
- Dependencies
- Example usage

---

## 1. Data Collection Component

### BinanceClient (`src/data_collection/binance_client.py`)

**Responsibility:** Interface to Binance Exchange

**Key Features:**
- REST API wrapper using CCXT & python-binance
- Rate limiting (10 calls/60s)
- Auto-retry with exponential backoff
- Error handling

**Public Methods:**

```python
def ping() -> bool:
    """Check API connection"""

def get_price(symbol: str) -> float:
    """Get current price"""

def get_ticker(symbol: str) -> dict:
    """Get 24h statistics"""

def get_historical_klines(symbol, interval, start_time, limit) -> pd.DataFrame:
    """Get OHLCV data"""

def create_market_order(symbol, side, quantity) -> dict:
    """Place market order"""

def create_oco_order(symbol, side, quantity, stop_price, price) -> dict:
    """Place OCO (TP+SL)"""

def get_account_balance() -> dict:
    """Get account balance"""
```

**Usage Example:**
```python
from src.data_collection import binance_client

# Get price
price = binance_client.get_price("BTC/USDT")

# Get historical data
df = binance_client.get_historical_klines(
    symbol="BTC/USDT",
    interval="1h",
    limit=100
)
```

---

### WebSocketCollector (`src/data_collection/websocket_collector.py`)

**Responsibility:** Real-time price streaming

**Architecture:**
- Runs in separate thread
- Event-driven callbacks
- Auto-reconnection
- Thread-safe

**Key Methods:**

```python
def start():
    """Start WebSocket connection"""

def stop():
    """Stop gracefully"""

def on(event_type: str, callback: Callable):
    """Register callback"""
    # event_type: 'kline', 'trade', 'ticker'

def _handle_kline_message(msg):
    """Process candlestick updates"""
```

**Event Data Format:**
```python
kline_data = {
    'symbol': 'BTC/USDT',
    'timestamp': datetime(...),
    'open': 45000.0,
    'high': 45100.0,
    'low': 44900.0,
    'close': 45050.0,
    'volume': 123.45,
    'is_closed': True  # Candlestick completed
}
```

---

## 2. Database Component

### DatabaseManager (`src/database/database.py`)

**Responsibility:** Database connection & session management

**Key Features:**
- SQLAlchemy ORM
- Context manager for transactions
- Connection pooling
- Error handling

**API:**

```python
class DatabaseManager:
    def session_scope(self):
        """Context manager for transactions"""
        # Auto-commit or rollback

    def check_connection(self) -> bool:
        """Health check"""

    def get_table_count(self, table_name: str) -> int:
        """Row count"""
```

**Usage:**
```python
from src.database import db

with db.session_scope() as session:
    trades = session.query(Trade).all()
    # Auto-commit on exit
```

---

### Repository Pattern

**TradeRepository (`src/database/repositories.py`)**

**Benefits:**
- Decoupling data access from business logic
- Reusable queries
- Easy testing (mock repositories)

**Methods:**

```python
class TradeRepository:
    @staticmethod
    def get_open_trades(session, symbol=None):
        """Get all open trades"""

    @staticmethod
    def get_closed_trades(session, symbol=None, days=30):
        """Get closed trades in last N days"""

    @staticmethod
    def get_performance_summary(session, days=30):
        """Calculate performance metrics"""
        return {
            'total_trades': int,
            'winning_trades': int,
            'losing_trades': int,
            'win_rate': float,
            'total_pnl': float,
            'avg_pnl': float,
            'largest_win': float,
            'largest_loss': float
        }

    @staticmethod
    def get_equity_curve(session, days=30):
        """Get cumulative P/L over time"""
```

---

## 3. Feature Engineering Component

### TechnicalIndicators (`src/feature_engineering/indicators.py`)

**Responsibility:** Calculate technical indicators

**Architecture:**
- Static methods (no state)
- Operates on pandas DataFrames
- Uses `ta` and `pandas-ta` libraries

**Categories:**

#### Momentum Indicators
```python
@staticmethod
def add_momentum_indicators(df):
    # RSI (14, 28 periods)
    # Stochastic Oscillator
    # Williams %R
    # ROC (Rate of Change)
    # CCI (Commodity Channel Index)
    return df
```

#### Trend Indicators
```python
@staticmethod
def add_trend_indicators(df):
    # EMA (9, 21, 50, 200)
    # SMA (20, 50, 200)
    # MACD (12, 26, 9)
    # ADX (Average Directional Index)
    # Aroon indicator
    return df
```

#### Volatility Indicators
```python
@staticmethod
def add_volatility_indicators(df):
    # Bollinger Bands (20, 2 std)
    # ATR (Average True Range 14)
    # Keltner Channels
    return df
```

#### Volume Indicators
```python
@staticmethod
def add_volume_indicators(df):
    # OBV (On-Balance Volume)
    # VWAP (Volume Weighted Average Price)
    # MFI (Money Flow Index)
    # Volume SMA and ratio
    return df
```

**Usage:**
```python
from src.feature_engineering import TechnicalIndicators

# Load OHLCV
df = get_ohlcv_data()

# Add all indicators
df = TechnicalIndicators.add_all_indicators(df)

# Access indicators
latest_rsi = df['rsi_14'].iloc[-1]
latest_macd = df['macd'].iloc[-1]
```

---

## 4. Machine Learning Component

### PriceClassifier (`src/models/classifier.py`)

**Responsibility:** Predict price direction

**Model:** XGBoost multi-class classifier

**Classes:**
- 0: DOWN (price will decrease)
- 1: NEUTRAL (sideways)
- 2: UP (price will increase)

**Training:**

```python
def train(self, df, test_size=0.2, horizon=6):
    """
    Train classifier

    Args:
        df: DataFrame with OHLCV + indicators
        test_size: Test split ratio
        horizon: Periods ahead to predict

    Returns:
        {
            'accuracy': 0.645,
            'classification_report': {...},
            'feature_importance': {...}
        }
    """
```

**Prediction:**

```python
def predict(self, df):
    """
    Predict price direction

    Returns:
        {
            'prediction': 'UP',  # or DOWN, NEUTRAL
            'confidence': 0.78,
            'probabilities': {
                'DOWN': 0.10,
                'NEUTRAL': 0.12,
                'UP': 0.78
            }
        }
    """
```

**Feature Engineering:**

```python
def _prepare_features(self, df, horizon=6):
    # Create lag features
    for col in ['close', 'volume', 'rsi_14', 'macd']:
        df[f'{col}_lag1'] = df[col].shift(1)
        df[f'{col}_lag2'] = df[col].shift(2)

    # Rolling statistics
    df['close_sma_5'] = df['close'].rolling(5).mean()
    df['close_std_5'] = df['close'].rolling(5).std()

    # Create labels
    df['future_return'] = df['close'].pct_change(horizon).shift(-horizon)
    df['label'] = df['future_return'].apply(lambda x:
        2 if x > 0.005 else 0 if x < -0.005 else 1
    )

    return df
```

---

## 5. Trading Engine Component

### SignalGenerator (`src/trading/signal_generator.py`)

**Responsibility:** Generate trading signals

**Strategy:** Ensemble of multiple strategies

**Architecture:**

```python
def generate_signal(df, predictions=None):
    # 1. Generate individual signals
    signals = {
        'technical': _technical_signal(df),
        'trend': _trend_signal(df),
        'mean_reversion': _mean_reversion_signal(df),
        'momentum': _momentum_signal(df),
    }

    # 2. Add ML signal if available
    if predictions:
        signals['ml'] = _ml_signal(predictions)

    # 3. Weighted voting
    combined = _combine_signals(signals)

    return combined
```

**Signal Types:**

```python
# Technical Signal
def _technical_signal(df):
    score = 0.5  # neutral

    if rsi < 30: score += 0.2  # oversold
    if macd > signal: score += 0.15  # bullish
    if close < bb_lower: score += 0.15  # below BB

    action = 'BUY' if score > 0.6 else 'SELL' if score < 0.4 else 'HOLD'
    return {'action': action, 'strength': abs(score - 0.5) * 2}

# Trend Signal
def _trend_signal(df):
    if ema_9 > ema_21 > ema_50:
        return {'action': 'BUY', 'strength': 0.9}
    elif ema_9 < ema_21 < ema_50:
        return {'action': 'SELL', 'strength': 0.9}
    else:
        return {'action': 'HOLD', 'strength': 0.3}
```

**Output:**
```python
{
    'action': 'BUY',  # or SELL, HOLD
    'confidence': 0.78,
    'reasoning': ['RSI oversold', 'MACD bullish', 'Strong uptrend'],
    'strength': 0.82,
    'buy_score': 0.78,
    'sell_score': 0.22
}
```

---

### EnhancedRiskManager (`src/trading/risk_manager_v2.py`)

**Responsibility:** Position sizing & risk management

**2024 Best Practices:**

1. **Fractional Kelly Criterion**
```python
# Calculate Kelly
kelly = (b * p - q) / b
where:
    b = win/loss ratio
    p = win probability
    q = 1 - p

# Apply fractional (1/10 for crypto)
fractional_kelly = kelly * 0.1

# Cap between 1% and 10%
fractional_kelly = max(0.01, min(fractional_kelly, 0.10))
```

2. **Hard Position Limits**
```python
max_single_position = 0.20  # 20% hard cap
final_size = min(calculated_size, account_balance * 0.20)
```

3. **Volatility Adjustment**
```python
atr_percent = (atr / price) * 100

if atr_percent < 1.0:
    volatility_factor = 1.2  # Low volatility → larger position
elif atr_percent < 2.0:
    volatility_factor = 1.0  # Normal
elif atr_percent < 3.0:
    volatility_factor = 0.8  # High → smaller position
else:
    volatility_factor = 0.6  # Very high → much smaller
```

**Main Method:**

```python
def calculate_optimal_position_size(
    account_balance,
    entry_price,
    stop_loss_price,
    confidence,
    atr=None,
    win_rate=None,
    avg_win=None,
    avg_loss=None
):
    # Method 1: Base (5% of portfolio)
    base_position = account_balance * 0.05

    # Method 2: Fractional Kelly
    kelly_position = _calculate_fractional_kelly(...)

    # Method 3: Risk-based
    risk_based = risk_amount / price_risk

    # Take minimum for safety
    optimal = min(base_position, kelly_position, risk_based)

    # Adjust by confidence
    adjusted = optimal * confidence

    # Volatility adjustment
    if atr:
        adjusted *= _calculate_volatility_factor(atr, entry_price)

    # Hard limit (20% max)
    final = min(adjusted, account_balance * 0.20)

    return final
```

---

### TradingExecutor (`src/trading/executor.py`)

**Responsibility:** Execute trades

**Modes:**
- **Paper:** Simulated trading (DB only)
- **Live:** Real orders on Binance

**Main Method:**

```python
def execute_signal(symbol, signal, account_balance):
    # 1. Calculate position size
    position_size = risk_manager.calculate_optimal_position_size(...)

    # 2. Convert to quantity
    quantity = position_size / current_price

    # 3. Calculate TP/SL
    if signal['action'] == 'BUY':
        stop_loss = entry_price * (1 - 0.005)
        take_profit = entry_price * (1 + 0.01)

    # 4. Execute based on mode
    if self.is_live:
        trade = _execute_live_trade(...)
    else:
        trade = _execute_paper_trade(...)

    # 5. Save to DB
    session.add(trade)
    session.commit()

    # 6. Alert
    telegram.send_trade_execution(...)

    return trade
```

**Paper Trade:**
```python
def _execute_paper_trade(...):
    trade = Trade(
        symbol=symbol,
        side=TradeSide.BUY,
        entry_price=current_price,
        quantity=quantity,
        stop_loss=stop_loss,
        take_profit=take_profit,
        status=TradeStatus.OPEN,
        is_paper_trade=True
    )
    return trade
```

**Live Trade:**
```python
def _execute_live_trade(...):
    # 1. Place market order
    order = binance_client.create_market_order(symbol, side, quantity)

    # 2. Place OCO (TP + SL)
    oco = binance_client.create_oco_order(
        symbol, 'SELL', quantity,
        stop_price=stop_loss,
        price=take_profit
    )

    # 3. Create trade record
    trade = Trade(..., order_id=order['orderId'], ...)

    return trade
```

---

## 6. Monitoring Component

### Logger (`src/utils/logger.py`)

**Configuration:**
```python
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Daily rotation
    retention="30 days",
    level="INFO"
)

logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    level="ERROR"
)
```

**Usage:**
```python
from src.utils import log

log.debug("Debug info")
log.info("Bot started")
log.warning("High drawdown detected")
log.error(f"Error: {e}")
log.critical("Critical system failure")
```

---

### TelegramNotifier (`src/utils/telegram_bot.py`)

**Methods:**

```python
def send_trade_execution(symbol, side, quantity, price):
    """
    🤖 Trade Executed

    Symbol: BTC/USDT
    Side: BUY
    Quantity: 0.006 BTC
    Price: $45,000.00
    ...
    """

def send_trade_close(symbol, exit_reason, pnl):
    """
    🎯 Trade Closed

    Symbol: BTC/USDT
    P/L: +$5.20 (+1.2%)
    Reason: TAKE_PROFIT
    """

def send_daily_summary():
    """
    📊 Daily Summary

    Total Trades: 5
    Win Rate: 60%
    Total P/L: +$12.30
    """
```

---

## Component Interaction Diagram

```
┌──────────────┐
│ Main Loop    │
└──────┬───────┘
       │
       ├──→ WebSocketCollector ──→ Database (OHLCV)
       │
       ├──→ OHLCVRepository ──→ Load recent data
       │
       ├──→ TechnicalIndicators ──→ Calculate features
       │
       ├──→ PriceClassifier ──→ ML prediction
       │
       ├──→ SignalGenerator ──→ Generate signal
       │         │
       │         ├─→ Technical strategy
       │         ├─→ Trend strategy
       │         ├─→ ML strategy
       │         └─→ Combine
       │
       ├──→ EnhancedRiskManager ──→ Position size
       │
       ├──→ TradingExecutor ──→ Execute trade
       │         │
       │         ├─→ Paper: Save to DB
       │         └─→ Live: Binance API
       │
       ├──→ Logger ──→ Log files
       │
       └──→ TelegramNotifier ──→ Alerts
```

---

## Next Steps

**Đọc tiếp:**
- [5. Trading Flow →](./05_trading_flow.md) - Workflow chi tiết
- [6. GUI Architecture →](./06_gui_architecture.md) - Desktop app

**Back to:** [Index](./README.md)

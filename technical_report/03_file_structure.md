# 3. File Structure

## Project Tree Overview

```
coin_pred/
├── config/                    # Configuration management
├── src/                       # Source code
│   ├── data_collection/       # Data from Binance
│   ├── database/              # ORM models & repositories
│   ├── feature_engineering/   # Technical indicators
│   ├── models/                # Machine Learning
│   ├── trading/               # Trading engine
│   ├── dashboard/             # Web UI (Streamlit)
│   ├── api/                   # REST API (FastAPI)
│   ├── gui/                   # Desktop app (PyQt5)
│   └── utils/                 # Utilities
├── scripts/                   # Utility scripts
├── data/                      # Data storage
├── logs/                      # Log files
├── tests/                     # Unit & integration tests
├── technical_report/          # This documentation
├── main_enhanced.py           # Main bot entry point
├── main_gui.py                # Desktop app entry point
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (secrets)
└── README.md                  # Project overview
```

---

## Core Files Explained

### Entry Points

#### `main_enhanced.py` ⭐
**Mục đích:** Main bot application - orchestrates everything

**Chức năng:**
- Initialize database, config, API connections
- Start WebSocket real-time data collection
- Run main trading loop
- Generate signals every N iterations
- Execute trades based on signals
- Monitor open positions
- Handle errors và graceful shutdown

**Key code:**
```python
def main():
    # 1. Setup
    init_database()
    collector = WebSocketCollector(symbols)
    collector.start()

    # 2. Main loop
    while True:
        if iteration % 10 == 0:  # Every 10 iterations
            for symbol in symbols:
                # Get data
                df = get_recent_data(symbol)
                # Calculate indicators
                df = add_indicators(df)
                # Generate signal
                signal = generate_signal(df)
                # Execute if confidence high
                if signal['confidence'] > 0.7:
                    execute_trade(signal)

        # Monitor open positions
        monitor_positions()

        time.sleep(10)
```

**Khi nào dùng:** Production trading (both paper & live)

---

#### `main_gui.py` ⭐
**Mục đích:** Desktop application entry point

**Chức năng:**
- Create PyQt5 application
- Show splash screen
- Initialize main window
- Start background workers
- Run GUI event loop

**Khi nào dùng:** Desktop monitoring & control

---

### Configuration

#### `config/config.py`
**Mục đích:** Type-safe configuration management

**Contents:**
```python
class TradingConfig(BaseSettings):
    trading_mode: Literal["paper", "live"] = "paper"
    target_symbols: List[str] = ["BTC/USDT", "ETH/USDT"]
    max_position_size: float = 0.05  # 5% of portfolio
    stop_loss_percent: float = 0.005  # 0.5%
    take_profit_percent: float = 0.01  # 1%
    min_confidence_score: float = 0.70
    max_concurrent_positions: int = 3
    max_daily_loss: float = 0.10  # 10%

class Settings(BaseSettings):
    binance: BinanceConfig
    trading: TradingConfig
    system: SystemConfig
    telegram: TelegramConfig

settings = Settings()
```

**Import:**
```python
from config import settings
symbols = settings.trading.target_symbols
```

---

#### `.env`
**Format:**
```bash
# Binance
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=True

# Trading
TRADING_MODE=paper

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
TELEGRAM_CHAT_ID=987654321
ENABLE_TELEGRAM_ALERTS=True
```

**⚠️ SECURITY:** Never commit to git! Listed in `.gitignore`

---

## Data Collection Module

### `src/data_collection/binance_client.py`
**Class:** `BinanceClient`

**Methods:**
- `get_price(symbol)` - Current price
- `get_ticker(symbol)` - 24h statistics
- `get_historical_klines(symbol, interval, limit)` - OHLCV data
- `create_market_order(symbol, side, quantity)` - Place market order
- `create_oco_order(...)` - OCO for TP/SL
- `get_account_balance()` - Account info

**Decorators:**
- `@retry_on_failure` - Auto-retry on errors
- `@rate_limit` - Prevent API ban

**Example:**
```python
from src.data_collection import binance_client

price = binance_client.get_price("BTC/USDT")
df = binance_client.get_historical_klines("BTC/USDT", "1h", limit=100)
```

---

### `src/data_collection/websocket_collector.py`
**Class:** `WebSocketCollector`

**Purpose:** Real-time price streaming

**Key methods:**
- `start()` - Start WebSocket connection
- `stop()` - Stop gracefully
- `on(event, callback)` - Register callback

**Usage:**
```python
collector = WebSocketCollector(["BTC/USDT", "ETH/USDT"])

def on_price_update(kline):
    print(f"New price: {kline['close']}")

collector.on('kline', on_price_update)
collector.start()
```

---

### `src/data_collection/historical_downloader.py`
**Purpose:** Bulk download historical data

**Usage:** Via script
```bash
python scripts/download_data.py --days 30 --interval 1h
```

---

## Database Module

### `src/database/models.py`
**All SQLAlchemy models:**

**OHLCV:**
```python
class OHLCV(Base):
    __tablename__ = "ohlcv"
    id, symbol, timeframe, timestamp
    open, high, low, close, volume
```

**Trade:**
```python
class Trade(Base):
    __tablename__ = "trades"
    id, symbol, side, entry_price, exit_price
    quantity, stop_loss, take_profit
    status, confidence_score
    gross_profit_loss, net_profit_loss
    entry_time, exit_time
```

**Others:** Feature, Prediction, PerformanceMetrics, SystemLog

---

### `src/database/repositories.py`
**Repository pattern for clean data access**

**TradeRepository:**
```python
@staticmethod
def get_open_trades(session, symbol=None):
    query = session.query(Trade).filter(Trade.status == TradeStatus.OPEN)
    return query.all()

@staticmethod
def get_performance_summary(session, days=30):
    # Calculate win rate, total P/L, etc.
    return {...}
```

**OHLCVRepository:**
```python
@staticmethod
def get_recent_data(session, symbol, timeframe, limit=100):
    # Return pandas DataFrame
    return df
```

---

### `src/database/database.py`
**Class:** `DatabaseManager`

**Methods:**
- `session_scope()` - Context manager for transactions
- `check_connection()` - Health check
- `get_table_count(table_name)` - Statistics

**Usage:**
```python
from src.database import db

with db.session_scope() as session:
    trades = session.query(Trade).all()
```

---

## Feature Engineering Module

### `src/feature_engineering/indicators.py`
**Class:** `TechnicalIndicators`

**Static methods (50+):**
- `add_momentum_indicators(df)` - RSI, Stochastic, etc.
- `add_trend_indicators(df)` - EMA, MACD, ADX
- `add_volatility_indicators(df)` - BB, ATR, Keltner
- `add_volume_indicators(df)` - OBV, VWAP, MFI
- `add_all_indicators(df)` - All in one call

**Usage:**
```python
from src.feature_engineering import TechnicalIndicators

df = get_ohlcv_data()
df = TechnicalIndicators.add_all_indicators(df)
# Now df has rsi_14, macd, bb_upper, etc.
```

---

## Machine Learning Module

### `src/models/classifier.py`
**Class:** `PriceClassifier`

**Methods:**
- `train(df, test_size, horizon)` - Train XGBoost
- `predict(df)` - Get prediction
- `save_model(path)` - Serialize
- `load_model(path)` - Deserialize

**Usage:**
```python
from src.models import PriceClassifier

# Training
classifier = PriceClassifier()
metrics = classifier.train(df, test_size=0.2, horizon=6)

# Prediction
result = classifier.predict(current_features)
# → {'prediction': 'UP', 'confidence': 0.78, 'probabilities': {...}}
```

---

## Trading Module

### `src/trading/signal_generator.py`
**Class:** `SignalGenerator`

**Methods:**
- `generate_signal(df, predictions)` - Main entry point
- `_technical_signal(df)` - Technical analysis
- `_trend_signal(df)` - Trend following
- `_mean_reversion_signal(df)` - Mean reversion
- `_momentum_signal(df)` - Momentum strategy
- `_combine_signals(signals)` - Weighted voting

**Output:**
```python
{
    'action': 'BUY',
    'confidence': 0.78,
    'reasoning': ['RSI oversold', 'MACD bullish'],
    'strength': 0.82
}
```

---

### `src/trading/risk_manager.py` (V1)
Basic risk management

### `src/trading/risk_manager_v2.py` ⭐ (V2 - RECOMMENDED)
**Class:** `EnhancedRiskManager`

**2024 best practices:**
- Fractional Kelly Criterion (1/10)
- Hard 20% position limit
- Volatility-based adjustments
- Monthly audits

**Key method:**
```python
position_size = risk_manager.calculate_optimal_position_size(
    account_balance,
    entry_price,
    stop_loss_price,
    confidence,
    atr,
    win_rate,
    avg_win,
    avg_loss
)
```

---

### `src/trading/executor.py`
**Class:** `TradingExecutor`

**Modes:**
- Paper trading (simulated)
- Live trading (real orders)

**Methods:**
- `execute_signal(symbol, signal, balance)` - Execute trade
- `_execute_paper_trade(...)` - Paper mode
- `_execute_live_trade(...)` - Live mode
- `monitor_positions()` - Check open trades

---

## GUI Module

### `src/gui/main_window.py`
**Class:** `MainWindow(QMainWindow)`

**Components:**
- Tab widget (Dashboard, Trading, Monitoring, History, Charts)
- Menu bar
- Status bar
- Background workers

---

### `src/gui/workers.py`
**QThread workers for non-blocking updates:**

- `PriceUpdateWorker` - Prices every 2s
- `OpenPositionsWorker` - Positions every 5s
- `TradeHistoryWorker` - On-demand
- `ChartDataWorker` - On-demand
- `PerformanceWorker` - On-demand
- `SystemStatsWorker` - Every 10s

---

### `src/gui/widgets/`
**Custom widgets:**
- `price_widget.py` - Real-time price table
- `trading_panel.py` - Start/stop controls
- `monitoring_widget.py` - Open positions
- `history_widget.py` - Trade history
- `chart_widget.py` - Candlestick charts

---

## Dashboard Module

### `src/dashboard/app.py`
Basic Streamlit dashboard

### `src/dashboard/app_v2.py` ⭐
Enhanced dashboard with:
- Custom CSS
- Multi-panel charts
- Advanced metrics
- Filtering

**Run:**
```bash
streamlit run src/dashboard/app_v2.py
```

---

## API Module

### `src/api/server.py`
**FastAPI REST API**

**Endpoints:**
- `GET /health` - System health
- `POST /bot/start` - Start bot
- `GET /prices/{symbol}` - Current price
- `GET /trades` - Trade history
- `GET /performance` - Metrics

**Run:**
```bash
python src/api/server.py
# or
uvicorn src.api.server:app --reload
```

**Docs:** http://localhost:8000/docs

---

## Utils Module

### `src/utils/logger.py`
**Logging configuration**

**Functions:**
- `log` - Main logger instance
- `log_trade()` - Log trades
- `log_prediction()` - Log ML predictions
- `log_error()` - Log errors

**Usage:**
```python
from src.utils import log

log.info("Bot started")
log.error(f"Error: {e}")
```

---

### `src/utils/helpers.py`
**Helper functions:**
- `calculate_position_size()` - Position sizing
- `calculate_profit_loss()` - P/L calculation
- `calculate_sharpe_ratio()` - Risk-adjusted return
- `safe_divide()` - Division with zero check
- `normalize_symbol()` - BTC/USDT → BTCUSDT

---

### `src/utils/telegram_bot.py`
**Class:** `TelegramNotifier`

**Methods:**
- `send_message(text)` - General message
- `send_trade_execution(...)` - Trade alert
- `send_trade_close(...)` - Close notification
- `send_error(...)` - Error alert
- `send_daily_summary()` - Daily stats

**Usage:**
```python
from src.utils import telegram

telegram.send_trade_execution("BTC/USDT", "BUY", 0.006, 45000)
```

---

## Scripts

### `scripts/init_db.py`
Initialize database tables
```bash
python scripts/init_db.py
```

### `scripts/download_data.py`
Download historical OHLCV data
```bash
python scripts/download_data.py --days 30 --interval 1h
```

### `scripts/train_models.py`
Train ML models
```bash
python scripts/train_models.py --interval 1h --horizon 6
```

### `scripts/health_check.py`
System health verification
```bash
python scripts/health_check.py
```

---

## Import Relationships

```
main_enhanced.py
├── config (settings)
├── src.database (db, repositories, models)
├── src.data_collection (binance_client, websocket_collector)
├── src.feature_engineering (indicators)
├── src.models (classifier)
├── src.trading (signal_generator, risk_manager_v2, executor)
└── src.utils (log, telegram)

main_gui.py
├── src.gui.main_window
│   ├── src.gui.widgets (all widgets)
│   ├── src.gui.workers (all workers)
│   ├── src.database
│   └── config
└── src.utils
```

---

## Data Files

```
data/
├── trading.db           # SQLite database
├── models/              # Saved ML models
│   ├── BTC_USDT_1h.pkl
│   └── ETH_USDT_1h.pkl
└── backups/             # DB backups (optional)
```

---

## Log Files

```
logs/
├── app_2025-01-17.log        # All logs
├── trading_2025-01-17.log    # Trading only
└── error_2025-01-17.log      # Errors only
```

Auto-rotation: Daily

---

## Documentation Files

```
/
├── README.md              # Project overview
├── QUICKSTART.md          # 5-minute setup
├── GUIDE.md               # Comprehensive guide
├── GUI_GUIDE.md           # Desktop app guide
├── OPTIMIZATIONS.md       # V2 improvements
└── technical_report/      # This documentation
```

---

## Next Steps

**Đọc tiếp:**
- [4. Core Components →](./04_core_components.md) - Deep dive vào components
- [2. Data Flow →](./02_data_flow.md) - Xem data chảy qua files này

**Back to:** [Index](./README.md)

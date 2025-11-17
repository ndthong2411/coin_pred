# 1. System Architecture

## Tổng quan

Crypto Trading Bot là một **automated trading system** với kiến trúc **modular, layered** được thiết kế để:
- Thu thập dữ liệu real-time từ Binance
- Phân tích kỹ thuật với 50+ indicators
- Dự đoán giá với Machine Learning
- Tự động thực hiện lệnh mua/bán
- Quản lý rủi ro với fractional Kelly Criterion
- Giám sát hiệu suất real-time

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Desktop    │  │   Streamlit  │  │  REST API    │          │
│  │     GUI      │  │   Dashboard  │  │   Server     │          │
│  │   (PyQt5)    │  │              │  │  (FastAPI)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MONITORING & ALERTS                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Logging    │  │   Telegram   │  │ Performance  │          │
│  │   (Loguru)   │  │     Bot      │  │   Metrics    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       TRADING ENGINE                            │
│  ┌────────────────────────────────────────────────────┐         │
│  │            Trading Orchestrator                     │         │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │         │
│  │  │  Signal  │  │   Risk   │  │ Executor │         │         │
│  │  │Generator │→ │ Manager  │→ │          │         │         │
│  │  └──────────┘  └──────────┘  └──────────┘         │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MACHINE LEARNING LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   XGBoost    │  │   Feature    │  │   Model      │          │
│  │  Classifier  │  │  Engineering │  │  Training    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA PROCESSING LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Technical   │  │  Indicators  │  │   Signals    │          │
│  │  Analysis    │  │  Calculator  │  │  Aggregator  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Binance    │  │  WebSocket   │  │  Historical  │          │
│  │  REST API    │  │   Real-time  │  │    Loader    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                          │
│  ┌────────────────────────────────────────────────────┐         │
│  │            SQLAlchemy ORM + SQLite                 │         │
│  │  ┌──────┐  ┌──────┐  ┌───────┐  ┌──────────┐     │         │
│  │  │OHLCV │  │Trades│  │Features│  │Predictions│     │         │
│  │  └──────┘  └──────┘  └───────┘  └──────────┘     │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  BINANCE EXCHANGE│
                    └──────────────────┘
```

---

## Layers Chi Tiết

### 1. **Data Collection Layer**

**Nhiệm vụ:** Thu thập dữ liệu thị trường từ Binance

**Components:**
- **BinanceClient** (`src/data_collection/binance_client.py`)
  - REST API wrapper
  - Get prices, tickers, historical data
  - Place orders, get balances

- **WebSocketCollector** (`src/data_collection/websocket_collector.py`)
  - Real-time price streams
  - Candlestick updates
  - Auto-reconnection logic

- **HistoricalDownloader** (`src/data_collection/historical_downloader.py`)
  - Bulk download historical OHLCV
  - Multiple timeframes
  - Data validation

**Data Flow:**
```
Binance Exchange → REST/WebSocket → Python Objects → Database
```

---

### 2. **Persistence Layer**

**Nhiệm vụ:** Lưu trữ và quản lý dữ liệu

**Technology:** SQLAlchemy ORM + SQLite (production có thể dùng PostgreSQL)

**Models:**
- **OHLCV** - Candlestick data (Open, High, Low, Close, Volume)
- **Trade** - Lịch sử giao dịch
- **Prediction** - ML predictions
- **Feature** - Calculated features
- **PerformanceMetrics** - Performance tracking
- **SystemLog** - System events

**Repository Pattern:**
```python
TradeRepository.get_open_trades(session)
TradeRepository.get_performance_summary(session, days=30)
OHLCVRepository.get_recent_data(session, symbol, timeframe, limit)
```

**Benefits:**
- Decoupling từ database implementation
- Easy testing với mock repositories
- Clean API cho data access

---

### 3. **Data Processing Layer**

**Nhiệm vụ:** Transform raw data thành actionable insights

**Components:**

1. **Technical Analysis** (`src/feature_engineering/indicators.py`)
   - 50+ technical indicators
   - RSI, MACD, Bollinger Bands, ATR, ADX, etc.
   - Momentum, Trend, Volatility, Volume indicators

2. **Feature Engineering** (`src/feature_engineering/feature_calculator.py`)
   - Calculate features từ OHLCV
   - Price action features
   - Statistical features
   - Time-based features

3. **Signal Aggregation**
   - Combine multiple signals
   - Weighted voting
   - Confidence scoring

**Example:**
```python
# Raw OHLCV
df = ohlcv_repository.get_recent_data(symbol, '1h', 100)

# Add indicators
df = TechnicalIndicators.add_all_indicators(df)

# Now df has: rsi_14, macd, bb_upper, atr_14, etc.
```

---

### 4. **Machine Learning Layer**

**Nhiệm vụ:** Predict price movements

**Components:**

1. **PriceClassifier** (`src/models/classifier.py`)
   - XGBoost multi-class classifier
   - Predicts: UP / DOWN / NEUTRAL
   - Returns confidence scores

2. **Feature Engineering for ML**
   - Lag features
   - Rolling statistics
   - Technical indicators as features

3. **Model Training** (`scripts/train_models.py`)
   - Train on historical data
   - Cross-validation
   - Feature importance analysis
   - Model persistence

**Workflow:**
```python
# 1. Prepare data
features = calculate_features(df)
labels = calculate_labels(df, horizon=6)  # 6 periods ahead

# 2. Train model
classifier = PriceClassifier()
classifier.train(features, labels)

# 3. Predict
prediction = classifier.predict(current_features)
# → {'prediction': 'UP', 'confidence': 0.78, 'probabilities': {...}}
```

---

### 5. **Trading Engine Layer**

**Nhiệm vụ:** Generate signals và execute trades

**Components:**

#### A. Signal Generator (`src/trading/signal_generator.py`)

Combines multiple strategies:

1. **Technical Signal**
   - RSI oversold/overbought
   - MACD crossovers
   - Bollinger Band touches

2. **Trend Signal**
   - EMA crossovers (9/21/50)
   - ADX strength
   - Trend direction

3. **Mean Reversion Signal**
   - Bollinger Band extremes
   - RSI extremes

4. **Momentum Signal**
   - Price momentum
   - Volume confirmation

5. **ML Signal** (if available)
   - Model predictions
   - High confidence trades

**Output:**
```python
{
    'action': 'BUY',  # or SELL, HOLD
    'confidence': 0.78,
    'reasoning': ['RSI oversold', 'MACD bullish', 'ML predicts UP'],
    'strength': 0.82
}
```

#### B. Risk Manager (`src/trading/risk_manager_v2.py`)

**V2 Features (2024 Best Practices):**

1. **Fractional Kelly Criterion**
   - 1/10 Kelly for crypto volatility
   - Conservative position sizing

2. **Hard Position Limits**
   - Max 20% per trade
   - Max concurrent positions

3. **Dynamic Volatility Adjustment**
   - ATR-based position scaling
   - High volatility → smaller positions

4. **Drawdown Protection**
   - Daily loss limits
   - Max portfolio drawdown

5. **Monthly Audits**
   - Performance review
   - Strategy validation

**Position Sizing:**
```python
position_size = risk_manager.calculate_optimal_position_size(
    account_balance=10000,
    entry_price=45000,
    stop_loss_price=44500,
    confidence=0.78,
    atr=500,
    win_rate=0.60
)
# → Takes min(Kelly, Risk-based, Hard limit)
```

#### C. Trading Executor (`src/trading/executor.py`)

**Modes:**
- **Paper Trading**: Simulated execution, saves to DB
- **Live Trading**: Real orders on Binance

**Order Types:**
- Market orders (immediate execution)
- OCO orders (One-Cancels-Other for TP/SL)

**Safety Checks:**
- Balance verification
- Symbol validation
- Minimum quantity checks
- Rate limiting

---

### 6. **Monitoring & Alerts Layer**

**Components:**

1. **Logging** (`src/utils/logger.py`)
   - Structured logging với Loguru
   - Multiple handlers (console, file, rotation)
   - Log levels (DEBUG, INFO, WARNING, ERROR)
   - Automatic log rotation

2. **Telegram Bot** (`src/utils/telegram_bot.py`)
   - Trade notifications
   - Error alerts
   - Daily summaries
   - Heartbeat signals

3. **Performance Tracking**
   - Win rate calculation
   - P/L tracking
   - Sharpe ratio
   - Max drawdown

---

### 7. **User Interface Layer**

#### A. Desktop GUI (`src/gui/`)

**Architecture: PyQt5 với QThread workers**

**Main Components:**
- **MainWindow** - Application shell
- **PriceWidget** - Real-time prices
- **TradingPanel** - Bot controls
- **MonitoringWidget** - Live positions
- **HistoryWidget** - Trade history
- **ChartWidget** - Interactive charts

**Background Workers:**
- PriceUpdateWorker (2s interval)
- OpenPositionsWorker (5s interval)
- PerformanceWorker (on-demand)
- ChartDataWorker (on-demand)

**Benefits:**
- Non-blocking UI
- Fast rendering
- Professional UX

#### B. Streamlit Dashboard (`src/dashboard/app_v2.py`)

**Features:**
- Web-based monitoring
- Custom CSS styling
- Interactive Plotly charts
- Real-time metrics
- Filtering capabilities

#### C. REST API (`src/api/server.py`)

**FastAPI server for programmatic access**

**Endpoints:**
```
GET  /health
GET  /status
POST /bot/start
POST /bot/stop
GET  /prices/{symbol}
GET  /trades
GET  /performance
GET  /ohlcv/{symbol}
```

---

## Technology Stack

### Backend
- **Language:** Python 3.10+
- **Web Framework:** FastAPI, Streamlit
- **GUI Framework:** PyQt5
- **Database:** SQLAlchemy ORM + SQLite
- **ML Framework:** XGBoost, scikit-learn
- **API Client:** CCXT, python-binance

### Libraries

**Data Processing:**
- pandas, numpy - Data manipulation
- ta, pandas-ta - Technical indicators

**Machine Learning:**
- xgboost - Gradient boosting
- scikit-learn - ML utilities
- optuna - Hyperparameter tuning (planned)

**Visualization:**
- plotly - Interactive charts
- pyqtgraph - Fast real-time plots
- matplotlib, seaborn - Statistical plots

**Monitoring:**
- loguru - Logging
- python-telegram-bot - Notifications

**Development:**
- pytest - Testing
- black, flake8 - Code quality
- mypy - Type checking
- pre-commit - Git hooks

---

## Design Patterns

### 1. **Repository Pattern**

Abstraction layer cho database access:

```python
class TradeRepository:
    @staticmethod
    def get_open_trades(session, symbol=None):
        query = session.query(Trade).filter(Trade.status == TradeStatus.OPEN)
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.all()
```

**Benefits:**
- Decoupling business logic từ data access
- Easy testing
- Consistent API

### 2. **Strategy Pattern**

Multiple signal generation strategies:

```python
class SignalGenerator:
    def _technical_signal(self, df): ...
    def _trend_signal(self, df): ...
    def _mean_reversion_signal(self, df): ...
    def _momentum_signal(self, df): ...

    def generate_signal(self, df):
        signals = [
            self._technical_signal(df),
            self._trend_signal(df),
            ...
        ]
        return self._combine_signals(signals)
```

### 3. **Observer Pattern**

WebSocket callbacks:

```python
collector.on('kline', callback_function)
collector.on('trade', another_callback)
```

### 4. **Singleton Pattern**

Global instances:

```python
# Global database instance
db = DatabaseManager()

# Global risk manager
risk_manager = RiskManager()
```

### 5. **Factory Pattern**

Create objects based on config:

```python
def create_trading_executor(mode: str):
    if mode == 'paper':
        return PaperTradingExecutor()
    elif mode == 'live':
        return LiveTradingExecutor()
```

---

## Scalability Considerations

### Current Architecture (Single Instance)

**Good for:**
- Personal trading (1-10 symbols)
- Development/Testing
- Small capital (<$10K)

**Limitations:**
- Single machine
- SQLite limitations
- No horizontal scaling

### Future Scalability Options

#### 1. **Database Upgrade**
```
SQLite → PostgreSQL
- Better concurrent access
- Advanced queries
- Replication support
```

#### 2. **Microservices**
```
Monolith → Microservices
- Data Collection Service
- ML Prediction Service
- Trading Execution Service
- Monitoring Service
```

#### 3. **Message Queue**
```
Add RabbitMQ/Kafka
- Async processing
- Decoupled components
- Better fault tolerance
```

#### 4. **Containerization**
```
Docker + Kubernetes
- Easy deployment
- Horizontal scaling
- Load balancing
```

#### 5. **Cloud Deployment**
```
AWS/GCP/Azure
- Auto-scaling
- Managed services
- Global availability
```

---

## Security Architecture

### API Keys
- Stored in `.env` (never in code)
- Read-only access recommended
- IP whitelist on exchange
- Trading permissions only (no withdrawal)

### Code Security
- Input validation
- SQL injection prevention (ORM)
- Rate limiting
- Error handling

### Operational Security
- Audit logs
- Alert system
- Backup strategy
- Disaster recovery plan

---

## Performance Characteristics

### Latency
- **WebSocket updates:** <100ms
- **Signal generation:** <500ms
- **Order execution:** <1s (network dependent)
- **GUI updates:** <50ms (non-blocking)

### Throughput
- **Price updates:** 10 symbols @ 2s intervals
- **Signal generation:** Every 10 iterations (configurable)
- **Database writes:** Async, batched

### Resource Usage
- **CPU:** Low (~5-10% idle, 20-30% active)
- **RAM:** ~500MB-1GB
- **Disk:** Minimal (SQLite grows slowly)
- **Network:** Low (WebSocket + occasional REST)

---

## Error Handling Strategy

### Levels

1. **Retry with Backoff**
   - Network errors
   - API rate limits
   - Temporary failures

2. **Graceful Degradation**
   - ML model unavailable → Use technical signals only
   - WebSocket down → Fall back to REST polling
   - Telegram down → Log only

3. **Fail Fast**
   - Invalid configuration
   - Missing API keys
   - Critical errors

### Recovery

- Automatic reconnection (WebSocket)
- State persistence (Database)
- Alert notifications (Telegram)
- Manual intervention (Desktop GUI)

---

## Testing Strategy

### Unit Tests
- Individual functions
- Pure logic
- Mock external dependencies

### Integration Tests
- Component interactions
- Database operations
- API calls (testnet)

### E2E Tests
- Full trading workflow
- Paper trading validation
- Performance benchmarks

### Manual Testing
- Live trading (small amounts)
- UI/UX validation
- Edge case scenarios

---

## Monitoring Strategy

### Metrics Tracked

**Trading Metrics:**
- Total P/L
- Win rate
- Sharpe ratio
- Max drawdown
- Number of trades
- Average trade duration

**System Metrics:**
- API call success rate
- WebSocket uptime
- Database response time
- Error rate
- Memory usage

**Business Metrics:**
- Daily returns
- Monthly performance
- Symbol performance
- Strategy effectiveness

### Alerts

**Critical:**
- Bot stopped unexpectedly
- Account balance < threshold
- API connection lost
- Database errors

**Warning:**
- High drawdown
- Low win rate
- API rate limit approaching
- Disk space low

**Info:**
- Trade executed
- Daily summary
- Heartbeat (bot alive)

---

## Configuration Management

### Environment Variables (`.env`)
```bash
# API Keys
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=xxx

# Mode
BINANCE_TESTNET=True
TRADING_MODE=paper

# Alerts
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
```

### Application Config (`config/config.py`)
```python
class TradingConfig:
    trading_mode: Literal["paper", "live"]
    max_position_size: float = 0.05
    stop_loss_percent: float = 0.005
    take_profit_percent: float = 0.01
    min_confidence_score: float = 0.70
```

### Benefits
- Type-safe configuration
- Validation on load
- Environment-specific settings
- Easy to modify without code changes

---

## Next Steps

**Đọc tiếp:**
- [2. Data Flow →](./02_data_flow.md) - Hiểu data chảy như thế nào
- [4. Core Components →](./04_core_components.md) - Deep dive vào components

**Back to:** [Index](./README.md)

# 2. Data Flow

## Tổng quan

Document này giải thích **chi tiết luồng dữ liệu** từ lúc bắt đầu cho đến khi trade được thực hiện và monitor.

**Mục tiêu:** Sau khi đọc, bạn sẽ hiểu:
- Data đi từ đâu đến đâu
- Qua những bước xử lý nào
- Lưu ở đâu, format ra sao
- Làm thế nào để trace data khi debug

---

## Complete Data Flow Diagram

```
┌─────────────────┐
│ BINANCE EXCHANGE│
└────────┬────────┘
         │
         ├─── WebSocket (Real-time)
         │    └─→ Price updates (every 1s)
         │
         └─── REST API (Historical)
              └─→ OHLCV data (bulk)

         ▼
┌─────────────────────────────────┐
│   DATA COLLECTION MODULE        │
│   (src/data_collection/)        │
├─────────────────────────────────┤
│ • BinanceClient                 │
│ • WebSocketCollector            │
│ • HistoricalDownloader          │
└────────┬────────────────────────┘
         │
         │ [OHLCV DataFrame]
         │ columns: timestamp, open, high, low, close, volume
         │
         ▼
┌─────────────────────────────────┐
│   DATABASE (PERSISTENCE)        │
│   SQLite + SQLAlchemy ORM       │
├─────────────────────────────────┤
│ Table: ohlcv                    │
│ • symbol, timeframe             │
│ • timestamp, ohlc, volume       │
└────────┬────────────────────────┘
         │
         │ [Query recent data]
         │ SELECT * FROM ohlcv WHERE...
         │
         ▼
┌─────────────────────────────────┐
│   FEATURE ENGINEERING           │
│   (src/feature_engineering/)    │
├─────────────────────────────────┤
│ • Add 50+ indicators            │
│ • RSI, MACD, BB, ATR, etc.      │
│ • Price action features         │
└────────┬────────────────────────┘
         │
         │ [Enhanced DataFrame]
         │ + rsi_14, macd, bb_upper, atr_14, ...
         │
         ├──────────────┬──────────────┐
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────────┐
    │   ML    │   │Technical│   │   Trend     │
    │  Model  │   │ Signal  │   │   Signal    │
    │         │   │Generator│   │  Generator  │
    └────┬────┘   └────┬────┘   └─────┬───────┘
         │             │              │
         │             │              │
         └─────────────┴──────────────┘
                       │
                       │ [Multiple Signals]
                       │
                       ▼
            ┌─────────────────────┐
            │  SIGNAL AGGREGATOR  │
            │  (Weighted Voting)  │
            └──────────┬──────────┘
                       │
                       │ [Combined Signal]
                       │ {action: BUY, confidence: 0.78}
                       │
                       ▼
            ┌─────────────────────┐
            │   RISK MANAGER V2   │
            │ • Position sizing   │
            │ • Fractional Kelly  │
            │ • Hard limits       │
            └──────────┬──────────┘
                       │
                       │ [Trade Parameters]
                       │ {symbol, side, quantity, stop_loss, take_profit}
                       │
                       ▼
            ┌─────────────────────┐
            │  TRADING EXECUTOR   │
            │ • Paper / Live mode │
            │ • Order placement   │
            └──────────┬──────────┘
                       │
                       ├─── Paper Mode ──→ Save to DB only
                       │
                       └─── Live Mode ───→ Binance API
                                            │
                       ┌────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   DATABASE (Trades) │
            │   Table: trades     │
            └──────────┬──────────┘
                       │
                       ├────→ Monitoring
                       ├────→ Performance Tracking
                       └────→ GUI Display
```

---

## Phase 1: Data Collection

### 1.1 Initial Historical Data Download

**Command:**
```bash
python scripts/download_data.py --days 30 --interval 1h
```

**Flow:**

```python
# scripts/download_data.py

# 1. Read config
symbols = settings.trading.target_symbols  # ['BTC/USDT', 'ETH/USDT', ...]
days = 30
interval = '1h'

# 2. Loop through symbols
for symbol in symbols:

    # 3. Calculate start_time
    start_time = datetime.now() - timedelta(days=days)

    # 4. Fetch from Binance
    df = binance_client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_time=start_time,
        limit=1000  # Binance max per request
    )

    # 5. df is a DataFrame:
    # ┌────────────────────┬──────┬──────┬──────┬──────┬────────┐
    # │ timestamp          │ open │ high │ low  │ close│ volume │
    # ├────────────────────┼──────┼──────┼──────┼──────┼────────┤
    # │ 2024-12-18 00:00:00│45000 │45100 │44900 │45050 │ 123.45 │
    # │ 2024-12-18 01:00:00│45050 │45200 │45000 │45150 │ 234.56 │
    # │ ...                │ ...  │ ...  │ ...  │ ...  │  ...   │
    # └────────────────────┴──────┴──────┴──────┴──────┴────────┘

    # 6. Save to database
    with db.session_scope() as session:
        for timestamp, row in df.iterrows():
            ohlcv = OHLCV(
                symbol=symbol,
                timeframe=interval,
                timestamp=timestamp,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            session.add(ohlcv)
        session.commit()
```

**Result:**
- Database table `ohlcv` populated
- Có historical data để train model và backtest

---

### 1.2 Real-time Data Collection (WebSocket)

**Start:**
```python
# In main_enhanced.py

collector = WebSocketCollector(symbols=settings.trading.target_symbols)

# Register callback
def on_kline_update(kline_data):
    # kline_data = {
    #     'symbol': 'BTC/USDT',
    #     'timestamp': datetime(...),
    #     'open': 45000.0,
    #     'high': 45100.0,
    #     'low': 44900.0,
    #     'close': 45050.0,
    #     'volume': 123.45,
    #     'is_closed': True
    # }

    if kline_data['is_closed']:
        # Candlestick completed, save to DB
        save_to_database(kline_data)

collector.on('kline', on_kline_update)
collector.start()
```

**Flow:**

```
WebSocket Stream (Binance)
    │
    ▼
[Raw JSON message]
{
  "e": "kline",
  "s": "BTCUSDT",
  "k": {
    "t": 1640000000000,
    "o": "45000.00",
    "h": "45100.00",
    "l": "44900.00",
    "c": "45050.00",
    "v": "123.45",
    "x": true
  }
}
    │
    ▼
[Parse & Transform]
WebSocketCollector._handle_kline_message()
    │
    ▼
[Python Dict]
{
  'symbol': 'BTC/USDT',
  'timestamp': datetime(2021, 12, 20, 12, 0, 0),
  'open': 45000.0,
  'high': 45100.0,
  'low': 44900.0,
  'close': 45050.0,
  'volume': 123.45,
  'is_closed': True
}
    │
    ▼
[Trigger Callback]
on_kline_update(kline_data)
    │
    ▼
[Save to Database]
INSERT INTO ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume)
VALUES ('BTC/USDT', '1m', '2021-12-20 12:00:00', 45000, 45100, 44900, 45050, 123.45)
```

**Kết quả:**
- Database liên tục được update với real-time data
- Có candlestick mới nhất để analyze

---

## Phase 2: Feature Engineering

### 2.1 Load Recent Data

**Code:**
```python
# In main_enhanced.py or signal generation

with db.session_scope() as session:
    df = OHLCVRepository.get_recent_data(
        session,
        symbol='BTC/USDT',
        timeframe='1h',
        limit=100  # Last 100 candles
    )

# df là DataFrame:
# ┌────────────────────┬──────┬──────┬──────┬──────┬────────┐
# │ timestamp          │ open │ high │ low  │ close│ volume │
# ├────────────────────┼──────┼──────┼──────┼──────┼────────┤
# │ 2025-01-15 00:00:00│44000 │44500 │43900 │44200 │ 100.0  │
# │ 2025-01-15 01:00:00│44200 │44600 │44100 │44500 │ 150.0  │
# │ ...                │ ...  │ ...  │ ...  │ ...  │  ...   │
# │ 2025-01-17 12:00:00│45000 │45100 │44900 │45050 │ 123.45 │ ← Latest
# └────────────────────┴──────┴──────┴──────┴──────┴────────┘
```

### 2.2 Calculate Indicators

**Code:**
```python
from src.feature_engineering import TechnicalIndicators

# Add all indicators
df = TechnicalIndicators.add_all_indicators(df)

# Now df has 50+ new columns:
# ┌──────┬───────┬───────┬────────┬───────┬────────┬─────┬─────┐
# │ close│ rsi_14│ macd  │macd_sig│bb_upper│bb_lower│ ...│ ... │
# ├──────┼───────┼───────┼────────┼───────┼────────┼─────┼─────┤
# │44200 │  45.2 │  12.5 │  10.3  │ 44800 │ 43600  │ ... │ ... │
# │44500 │  52.3 │  15.2 │  11.8  │ 45000 │ 43800  │ ... │ ... │
# │...   │  ...  │  ...  │  ...   │  ...  │  ...   │ ... │ ... │
# │45050 │  58.7 │  18.9 │  14.2  │ 45300 │ 44200  │ ... │ ... │
# └──────┴───────┴───────┴────────┴───────┴────────┴─────┴─────┘
```

**Indicators Added:**

**Momentum:**
- rsi_14, rsi_28
- stochastic_k, stochastic_d
- williams_r
- roc (Rate of Change)
- cci (Commodity Channel Index)

**Trend:**
- ema_9, ema_21, ema_50, ema_200
- sma_20, sma_50, sma_200
- macd, macd_signal, macd_histogram
- adx (Average Directional Index)
- aroon_up, aroon_down

**Volatility:**
- bb_upper, bb_middle, bb_lower
- bb_pct (position within bands)
- atr_14 (Average True Range)
- keltner_upper, keltner_lower

**Volume:**
- obv (On-Balance Volume)
- vwap (Volume Weighted Average Price)
- mfi (Money Flow Index)
- volume_sma, volume_ratio

**Price Action:**
- price_change, price_change_pct
- high_low_range
- close_open_diff

---

### 2.3 Feature Storage (Optional)

Có thể lưu features vào database để reuse:

```python
# Save to features table
feature = Feature(
    symbol='BTC/USDT',
    timestamp=latest_timestamp,
    feature_name='rsi_14',
    feature_value=58.7
)
session.add(feature)
```

**Trade-off:**
- **Pros:** Không cần recalculate mỗi lần
- **Cons:** Database size lớn hơn
- **Current approach:** Calculate on-the-fly (fast enough)

---

## Phase 3: Signal Generation

### 3.1 Multiple Signal Strategies

```python
from src.trading import signal_generator

# Generate signal
signal = signal_generator.generate_signal(
    df=df,  # DataFrame with indicators
    predictions=ml_predictions  # Optional ML predictions
)

# signal = {
#     'action': 'BUY',  # or SELL, HOLD
#     'confidence': 0.78,
#     'reasoning': ['RSI oversold', 'MACD bullish', 'Strong uptrend'],
#     'strength': 0.82,
#     'individual_signals': {
#         'technical': {'action': 'BUY', 'strength': 0.8},
#         'trend': {'action': 'BUY', 'strength': 0.9},
#         'ml': {'action': 'BUY', 'confidence': 0.75}
#     }
# }
```

### 3.2 Signal Generation Logic

**Step 1: Technical Signal**

```python
def _technical_signal(self, df):
    latest = df.iloc[-1]

    reasons = []
    score = 0.5  # Neutral

    # RSI
    if latest['rsi_14'] < 30:
        reasons.append("RSI oversold")
        score += 0.2
    elif latest['rsi_14'] > 70:
        reasons.append("RSI overbought")
        score -= 0.2

    # MACD
    if latest['macd'] > latest['macd_signal']:
        reasons.append("MACD bullish")
        score += 0.15
    elif latest['macd'] < latest['macd_signal']:
        reasons.append("MACD bearish")
        score -= 0.15

    # Bollinger Bands
    if latest['close'] < latest['bb_lower']:
        reasons.append("Below BB lower band")
        score += 0.15
    elif latest['close'] > latest['bb_upper']:
        reasons.append("Above BB upper band")
        score -= 0.15

    # Convert score to action
    if score > 0.6:
        action = 'BUY'
    elif score < 0.4:
        action = 'SELL'
    else:
        action = 'HOLD'

    return {
        'action': action,
        'strength': abs(score - 0.5) * 2,  # 0-1 scale
        'reasoning': reasons
    }
```

**Step 2: Trend Signal**

```python
def _trend_signal(self, df):
    latest = df.iloc[-1]

    # EMA crossovers
    ema_9 = latest['ema_9']
    ema_21 = latest['ema_21']
    ema_50 = latest['ema_50']

    # Strong uptrend
    if ema_9 > ema_21 > ema_50:
        return {'action': 'BUY', 'strength': 0.9}

    # Strong downtrend
    elif ema_9 < ema_21 < ema_50:
        return {'action': 'SELL', 'strength': 0.9}

    # Weak trend
    else:
        return {'action': 'HOLD', 'strength': 0.3}
```

**Step 3: ML Signal (if available)**

```python
def _ml_signal(self, predictions):
    if not predictions:
        return None

    action = predictions['prediction']  # UP, DOWN, NEUTRAL
    confidence = predictions['confidence']

    if action == 'UP' and confidence > 0.7:
        return {'action': 'BUY', 'confidence': confidence}
    elif action == 'DOWN' and confidence > 0.7:
        return {'action': 'SELL', 'confidence': confidence}
    else:
        return {'action': 'HOLD', 'confidence': confidence}
```

**Step 4: Combine Signals**

```python
def _combine_signals(self, signals, latest):
    # Weighted voting
    weights = {
        'technical': 0.3,
        'trend': 0.3,
        'mean_reversion': 0.2,
        'momentum': 0.1,
        'ml': 0.1
    }

    buy_score = 0
    sell_score = 0

    for signal_type, signal in signals.items():
        weight = weights.get(signal_type, 0.1)

        if signal['action'] == 'BUY':
            buy_score += weight * signal.get('strength', 0.5)
        elif signal['action'] == 'SELL':
            sell_score += weight * signal.get('strength', 0.5)

    # Determine final action
    if buy_score > sell_score and buy_score > 0.4:
        action = 'BUY'
        confidence = buy_score
    elif sell_score > buy_score and sell_score > 0.4:
        action = 'SELL'
        confidence = sell_score
    else:
        action = 'HOLD'
        confidence = max(buy_score, sell_score)

    return {
        'action': action,
        'confidence': min(confidence, 1.0),
        'buy_score': buy_score,
        'sell_score': sell_score
    }
```

---

## Phase 4: Risk Management

### 4.1 Position Size Calculation

**Input:**
```python
signal = {
    'action': 'BUY',
    'confidence': 0.78
}

account_balance = 10000  # $10,000
entry_price = 45000
stop_loss_price = 44500  # -1.1%
atr = 500
```

**Processing:**

```python
position_size = risk_manager.calculate_optimal_position_size(
    account_balance=10000,
    entry_price=45000,
    stop_loss_price=44500,
    confidence=0.78,
    atr=500,
    win_rate=0.60,  # Historical
    avg_win=150,     # Historical
    avg_loss=100     # Historical
)

# Internal calculations:
# 1. Base position = 10000 * 0.05 = $500
# 2. Kelly = (0.60 * 150/100 - 0.40) / (150/100) ≈ 0.33
#    Fractional Kelly = 0.33 * 0.1 = 0.033 → $330
# 3. Risk-based = (10000 * 0.05) / (45000 - 44500) = $500 / $500 = 1 BTC → $45000 (too high, capped)
# 4. Take minimum: min($500, $330, $10000*0.20) = $330
# 5. Adjust by confidence: $330 * 0.78 = $257.40
# 6. Volatility adjustment (ATR 500 / 45000 = 1.1% → normal) = 1.0x
# 7. Final = $257.40
```

**Output:**
```python
position_size = 257.40  # USD value
```

### 4.2 Trade Parameters Calculation

```python
# Convert to quantity
quantity = position_size / entry_price
# quantity = 257.40 / 45000 = 0.00572 BTC

# Round to exchange precision
quantity = round(quantity, 6)  # 0.005720 BTC

# Calculate stop loss and take profit
stop_loss = entry_price * (1 - 0.005)  # 0.5% stop loss
take_profit = entry_price * (1 + 0.01)  # 1% take profit

# stop_loss = 44775
# take_profit = 45450

trade_params = {
    'symbol': 'BTC/USDT',
    'side': 'BUY',
    'quantity': 0.005720,
    'entry_price': 45000,
    'stop_loss': 44775,
    'take_profit': 45450,
    'confidence': 0.78
}
```

---

## Phase 5: Trade Execution

### 5.1 Paper Trading Flow

```python
# src/trading/executor.py

trade = executor.execute_signal(
    symbol='BTC/USDT',
    signal=signal,
    account_balance=10000
)

# PAPER MODE:
# 1. Calculate position size (as above)
# 2. Create Trade object
trade = Trade(
    symbol='BTC/USDT',
    side=TradeSide.BUY,
    entry_price=45000,
    quantity=0.005720,
    stop_loss=44775,
    take_profit=45450,
    confidence_score=0.78,
    entry_time=datetime.utcnow(),
    status=TradeStatus.OPEN,
    is_paper_trade=True
)

# 3. Save to database
with db.session_scope() as session:
    session.add(trade)
    session.commit()

# 4. Log
log.info(f"📝 PAPER TRADE: BUY 0.005720 BTC/USDT @ $45000")

# 5. Send Telegram alert
telegram.send_trade_execution('BTC/USDT', 'BUY', 0.005720, 45000)
```

**Result:**
- Trade saved to database với status OPEN
- No real order on exchange
- Can monitor và track P/L

### 5.2 Live Trading Flow

```python
# LIVE MODE:
# 1. All safety checks
assert account_balance >= position_size
assert binance_client.ping()  # API alive

# 2. Place market order
order = binance_client.create_market_order(
    symbol='BTC/USDT',
    side='BUY',
    quantity=0.005720
)

# order response from Binance:
# {
#     'orderId': 123456789,
#     'symbol': 'BTCUSDT',
#     'status': 'FILLED',
#     'executedQty': '0.005720',
#     'cummulativeQuoteQty': '257.40',
#     'avgPrice': '45000.00'
# }

# 3. Place OCO order (stop-loss + take-profit)
oco_order = binance_client.create_oco_order(
    symbol='BTC/USDT',
    side='SELL',
    quantity=0.005720,
    stop_price=44775,      # Stop loss trigger
    stop_limit_price=44750, # Stop loss limit
    price=45450             # Take profit limit
)

# 4. Save trade to database
trade = Trade(
    symbol='BTC/USDT',
    side=TradeSide.BUY,
    entry_price=order['avgPrice'],
    quantity=order['executedQty'],
    stop_loss=44775,
    take_profit=45450,
    order_id=order['orderId'],
    oco_order_id=oco_order['orderListId'],
    entry_time=datetime.utcnow(),
    status=TradeStatus.OPEN,
    is_paper_trade=False
)

session.add(trade)
session.commit()

# 5. Alert
log.info(f"✅ LIVE TRADE EXECUTED: BUY 0.005720 BTC/USDT @ ${order['avgPrice']}")
telegram.send_trade_execution('BTC/USDT', 'BUY', 0.005720, order['avgPrice'])
```

---

## Phase 6: Position Monitoring

### 6.1 Check Open Positions

```python
# Every loop iteration (e.g., every 10s)

with db.session_scope() as session:
    open_trades = TradeRepository.get_open_trades(session)

    for trade in open_trades:
        # Get current price
        current_price = binance_client.get_price(trade.symbol)

        # Calculate unrealized P/L
        if trade.side == TradeSide.BUY:
            pnl = (current_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - current_price) * trade.quantity

        # Check if hit stop loss or take profit (paper trading)
        if trade.is_paper_trade:
            if trade.side == TradeSide.BUY:
                if current_price <= trade.stop_loss:
                    # Stop loss hit
                    close_paper_trade(trade, current_price, 'STOP_LOSS')
                elif current_price >= trade.take_profit:
                    # Take profit hit
                    close_paper_trade(trade, current_price, 'TAKE_PROFIT')
        else:
            # Live trading: OCO order will handle automatically
            # Just check if order is filled
            order_status = binance_client.get_order_status(trade.oco_order_id)
            if order_status == 'FILLED':
                close_live_trade(trade, order_status)
```

### 6.2 Close Trade

```python
def close_paper_trade(trade, exit_price, reason):
    trade.exit_price = exit_price
    trade.exit_time = datetime.utcnow()
    trade.status = TradeStatus.CLOSED

    # Calculate P/L
    if trade.side == TradeSide.BUY:
        gross_pnl = (exit_price - trade.entry_price) * trade.quantity
    else:
        gross_pnl = (trade.entry_price - exit_price) * trade.quantity

    # Subtract fees (0.1% per trade)
    fees = (trade.entry_price + exit_price) * trade.quantity * 0.001
    net_pnl = gross_pnl - fees

    trade.gross_profit_loss = gross_pnl
    trade.fees_paid = fees
    trade.net_profit_loss = net_pnl
    trade.profit_loss_percent = (net_pnl / (trade.entry_price * trade.quantity)) * 100

    session.commit()

    # Log
    log.info(f"🎯 Trade closed: {trade.symbol} | Reason: {reason} | P/L: ${net_pnl:.2f}")

    # Alert
    telegram.send_trade_close(trade.symbol, reason, net_pnl)
```

**Database Update:**

```
Before:
┌────┬──────────┬──────┬──────┬─────┬────────┬──────┐
│ id │  symbol  │ side │entry │ qty │ status │ exit │
├────┼──────────┼──────┼──────┼─────┼────────┼──────┤
│ 1  │ BTC/USDT │ BUY  │45000 │0.006│  OPEN  │ NULL │
└────┴──────────┴──────┴──────┴─────┴────────┴──────┘

After:
┌────┬──────────┬──────┬──────┬─────┬────────┬──────┬──────┐
│ id │  symbol  │ side │entry │ qty │ status │ exit │ P/L  │
├────┼──────────┼──────┼──────┼─────┼────────┼──────┼──────┤
│ 1  │ BTC/USDT │ BUY  │45000 │0.006│ CLOSED │45450 │+2.45 │
└────┴──────────┴──────┴──────┴─────┴────────┴──────┴──────┘
```

---

## Phase 7: Monitoring & Alerts

### 7.1 Logging

**Every significant event is logged:**

```python
# Data collection
log.debug("Received WebSocket kline: BTC/USDT @ 45050")

# Signal generation
log.info("Signal: BUY BTC/USDT (confidence: 0.78)")

# Trade execution
log.info("Trade executed: ID=123 BUY 0.006 BTC/USDT @ $45000")

# Position monitoring
log.debug("Monitoring 3 open positions")

# Trade close
log.info("Trade closed: ID=123 P/L=$+2.45 (+0.95%)")

# Errors
log.error("Failed to place order: Insufficient balance")
```

**Log files:**
```
logs/
├── app_2025-01-17.log       # All logs
├── trading_2025-01-17.log   # Trading-specific
└── error_2025-01-17.log     # Errors only
```

### 7.2 Telegram Alerts

**Trade Execution:**
```
🤖 Trade Executed

Symbol: BTC/USDT
Side: BUY
Quantity: 0.005720 BTC
Price: $45,000.00
Value: $257.40
Confidence: 78%
Stop Loss: $44,775
Take Profit: $45,450

Time: 2025-01-17 14:30:25
```

**Trade Close:**
```
🎯 Trade Closed

Symbol: BTC/USDT
Entry: $45,000.00
Exit: $45,450.00
Duration: 2h 15m
P/L: +$2.45 (+0.95%)
Reason: TAKE_PROFIT

Time: 2025-01-17 16:45:30
```

**Daily Summary:**
```
📊 Daily Summary - Jan 17, 2025

Total Trades: 5
Winning: 3 (60%)
Losing: 2 (40%)

Total P/L: +$12.30
Largest Win: +$5.20
Largest Loss: -$2.10

Win Rate: 60%
Account Balance: $10,012.30 (+0.12%)
```

---

## Phase 8: Performance Tracking

### 8.1 Calculate Metrics

```python
with db.session_scope() as session:
    summary = TradeRepository.get_performance_summary(session, days=30)

# summary = {
#     'total_trades': 150,
#     'winning_trades': 90,
#     'losing_trades': 60,
#     'win_rate': 0.60,
#     'total_pnl': 523.45,
#     'avg_pnl': 3.49,
#     'largest_win': 45.30,
#     'largest_loss': -23.10
# }
```

### 8.2 Display in GUI

**Desktop App:**
- Updates every 5 seconds
- Shows open positions
- Real-time P/L
- Performance metrics

**Streamlit Dashboard:**
- Updates every 10 seconds (auto-refresh)
- Charts và graphs
- Detailed analytics

**REST API:**
- `/performance` endpoint
- Programmatic access
- Integration với external systems

---

## Data Persistence Summary

### Tables and Relationships

```
┌─────────────┐
│    OHLCV    │
├─────────────┤        ┌─────────────┐
│ id          │───────>│   Trades    │
│ symbol      │        ├─────────────┤
│ timeframe   │        │ id          │
│ timestamp   │        │ symbol      │
│ open        │        │ side        │
│ high        │        │ entry_price │
│ low         │        │ exit_price  │
│ close       │        │ quantity    │
│ volume      │        │ status      │
└─────────────┘        │ pnl         │
                       └─────────────┘
                              │
                              │
                              ▼
                       ┌─────────────┐
                       │ Performance │
                       ├─────────────┤
                       │ Calculated  │
                       │ from Trades │
                       └─────────────┘
```

---

## Complete Flow Example

**Scenario:** Bot detects BUY signal và executes trade

```
1. [00:00] WebSocket receives new candle: BTC/USDT close at $45,050
           ↓
2. [00:01] Save to database: ohlcv table
           ↓
3. [00:02] Load last 100 candles from database
           ↓
4. [00:03] Calculate 50+ indicators
           ↓
5. [00:04] Generate signals from multiple strategies
           ↓
6. [00:05] Aggregate signals: BUY with 78% confidence
           ↓
7. [00:06] Risk manager calculates position size: 0.0057 BTC
           ↓
8. [00:07] Execute trade:
           - Paper mode: Save to DB only
           - Live mode: Place order on Binance
           ↓
9. [00:08] Save trade to trades table (status: OPEN)
           ↓
10. [00:09] Send Telegram alert
            ↓
11. [00:10] Log trade execution
            ↓
12. [Continuous] Monitor position
            - Check current price every 10s
            - Calculate unrealized P/L
            - Check if TP/SL hit
            ↓
13. [02:15] Take profit hit at $45,450
            ↓
14. [02:16] Close trade, update database (status: CLOSED)
            ↓
15. [02:17] Calculate final P/L: +$2.45
            ↓
16. [02:18] Send Telegram close notification
            ↓
17. [02:19] Update performance metrics
            ↓
18. [02:20] Display in GUI/Dashboard
```

---

## Next Steps

**Đọc tiếp:**
- [3. File Structure →](./03_file_structure.md) - Chi tiết từng file làm gì
- [5. Trading Flow →](./05_trading_flow.md) - Deep dive vào trading logic

**Back to:** [Index](./README.md)

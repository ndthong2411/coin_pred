# 5. Trading Flow

## Overview

This document explains the **complete trading workflow** từ khi bot start đến khi trade được close.

---

## Full Trading Cycle

```
[START BOT]
    │
    ▼
[Initialize]
├─→ Load config
├─→ Initialize database
├─→ Connect to Binance API
├─→ Load ML models (if available)
├─→ Start WebSocket
└─→ Log startup

    │
    ▼
[Main Loop] ←──────────────┐
    │                      │
    ├─→ [Data Collection]   │
    │    ├─→ WebSocket streams (real-time)
    │    └─→ Save to DB when candle closes
    │                      │
    ├─→ [Every N iterations (e.g., 10)]
    │    │                 │
    │    ├─→ [Signal Generation]
    │    │    ├─→ Load recent data
    │    │    ├─→ Calculate indicators
    │    │    ├─→ ML prediction (optional)
    │    │    ├─→ Generate signals
    │    │    └─→ Combine signals
    │    │         │
    │    │         ▼
    │    │    [Signal Quality Check]
    │    │    ├─→ Confidence > threshold?
    │    │    ├─→ Max positions reached?
    │    │    └─→ Daily loss limit?
    │    │         │
    │    │         ├─→ NO: Skip trade
    │    │         │
    │    │         └─→ YES: Continue
    │    │              │
    │    │              ▼
    │    ├─→ [Risk Management]
    │    │    ├─→ Calculate position size
    │    │    ├─→ Calculate stop loss
    │    │    ├─→ Calculate take profit
    │    │    └─→ Validate trade params
    │    │         │
    │    │         ▼
    │    └─→ [Trade Execution]
    │         ├─→ Paper: Save to DB
    │         ├─→ Live: Place order
    │         ├─→ Log trade
    │         └─→ Send alert
    │                      │
    ├─→ [Position Monitoring]
    │    └─→ For each open trade:
    │         ├─→ Get current price
    │         ├─→ Calculate unrealized P/L
    │         ├─→ Check TP/SL conditions
    │         └─→ Close if conditions met
    │                      │
    ├─→ [Sleep 10s] ───────┘
    │
    ▼
[User stops bot]
    │
    ▼
[Cleanup]
├─→ Stop WebSocket
├─→ Close open positions (optional)
├─→ Save final state
└─→ Log shutdown
```

---

## Detailed Step-by-Step

### Phase 1: Initialization

```python
def main():
    log.info("=" * 60)
    log.info("CRYPTO TRADING BOT - STARTING")
    log.info("=" * 60)

    # 1. Load configuration
    log.info(f"Mode: {settings.trading.trading_mode}")
    log.info(f"Symbols: {settings.trading.target_symbols}")

    # 2. Initialize database
    init_database()
    log.info("✅ Database initialized")

    # 3. Test Binance API connection
    if not binance_client.ping():
        log.error("❌ Failed to connect to Binance")
        sys.exit(1)
    log.info("✅ Binance API connected")

    # 4. Load ML models (optional)
    try:
        classifier = PriceClassifier()
        classifier.load_model("data/models/BTC_USDT_1h.pkl")
        log.info("✅ ML model loaded")
    except:
        log.warning("⚠️  ML model not found, using technical signals only")
        classifier = None

    # 5. Start WebSocket
    collector = WebSocketCollector(settings.trading.target_symbols)
    collector.on('kline', on_kline_update)
    collector.start()
    log.info("✅ WebSocket started")

    # 6. Send startup notification
    telegram.send_message("🤖 Bot started successfully!")

    log.info("=" * 60)
    log.info("🚀 Bot is running. Press Ctrl+C to stop.")
    log.info("=" * 60)
```

---

### Phase 2: Data Collection Loop

**WebSocket callback:**

```python
def on_kline_update(kline_data):
    """
    Called every time a new candlestick is received

    kline_data = {
        'symbol': 'BTC/USDT',
        'timestamp': datetime(...),
        'open': 45000,
        'high': 45100,
        'low': 44900,
        'close': 45050,
        'volume': 123.45,
        'is_closed': True
    }
    """

    # Only save completed candles
    if kline_data['is_closed']:
        with db.session_scope() as session:
            ohlcv = OHLCV(
                symbol=kline_data['symbol'],
                timeframe='1m',  # WebSocket gives 1m candles
                timestamp=kline_data['timestamp'],
                open=kline_data['open'],
                high=kline_data['high'],
                low=kline_data['low'],
                close=kline_data['close'],
                volume=kline_data['volume']
            )
            session.add(ohlcv)
            session.commit()

        log.debug(f"💾 Saved candle: {kline_data['symbol']} @ {kline_data['close']}")
```

---

### Phase 3: Signal Generation (Every N iterations)

```python
iteration = 0

while True:
    iteration += 1

    # Every 10 iterations (approximately every 100s if sleep=10s)
    if iteration % 10 == 0:
        log.info(f"--- Iteration {iteration} - Analyzing market ---")

        for symbol in settings.trading.target_symbols:
            try:
                process_symbol(symbol, classifier)
            except Exception as e:
                log.error(f"Error processing {symbol}: {e}")

    # Monitor positions every iteration
    monitor_open_positions()

    # Sleep
    time.sleep(10)


def process_symbol(symbol, classifier):
    """Process a single symbol for trading signals"""

    # Step 1: Load recent data
    log.debug(f"Loading data for {symbol}...")
    with db.session_scope() as session:
        df = OHLCVRepository.get_recent_data(
            session,
            symbol=symbol,
            timeframe='1h',
            limit=100
        )

    if df.empty or len(df) < 50:
        log.warning(f"Insufficient data for {symbol}")
        return

    # Step 2: Calculate indicators
    log.debug(f"Calculating indicators for {symbol}...")
    df = TechnicalIndicators.add_all_indicators(df)

    # Step 3: ML prediction (if available)
    ml_predictions = None
    if classifier:
        try:
            ml_predictions = classifier.predict(df)
            log.debug(f"ML Prediction: {ml_predictions['prediction']} ({ml_predictions['confidence']:.2%})")
        except Exception as e:
            log.warning(f"ML prediction failed: {e}")

    # Step 4: Generate signal
    signal = signal_generator.generate_signal(df, ml_predictions)

    log.info(f"📊 {symbol} | Signal: {signal['action']} | Confidence: {signal['confidence']:.2%}")

    if signal['reasoning']:
        log.info(f"   Reasons: {', '.join(signal['reasoning'])}")

    # Step 5: Execute if signal strong enough
    if signal['action'] != 'HOLD' and signal['confidence'] >= settings.trading.min_confidence_score:
        execute_if_allowed(symbol, signal)
    else:
        log.debug(f"   Signal not strong enough or HOLD, skipping trade")
```

---

### Phase 4: Pre-Trade Validation

```python
def execute_if_allowed(symbol, signal):
    """Check if trade is allowed before executing"""

    with db.session_scope() as session:
        # Check 1: Max concurrent positions
        open_trades = TradeRepository.get_open_trades(session)
        if len(open_trades) >= settings.trading.max_concurrent_positions:
            log.warning(f"⚠️  Max concurrent positions reached ({len(open_trades)}), skipping trade")
            return

        # Check 2: Already have open position in this symbol?
        open_trades_symbol = TradeRepository.get_open_trades(session, symbol=symbol)
        if open_trades_symbol:
            log.debug(f"Already have open position in {symbol}, skipping")
            return

        # Check 3: Daily loss limit
        today_summary = TradeRepository.get_performance_summary(session, days=1)
        if today_summary['total_pnl'] < -settings.trading.max_daily_loss * get_account_balance():
            log.error(f"❌ Daily loss limit reached (${today_summary['total_pnl']:.2f}), stopping trading")
            return

        # All checks passed, execute trade
        execute_trade(symbol, signal, session)
```

---

### Phase 5: Risk Management & Execution

```python
def execute_trade(symbol, signal, session):
    """Execute a trade with proper risk management"""

    # Get current price and balance
    current_price = binance_client.get_price(symbol)
    account_balance = get_account_balance()

    log.info(f"💰 Account balance: ${account_balance:.2f}")
    log.info(f"📌 Current price: ${current_price:.2f}")

    # Calculate position size
    stop_loss_price = current_price * (1 - settings.trading.stop_loss_percent) if signal['action'] == 'BUY' else current_price * (1 + settings.trading.stop_loss_percent)

    # Get ATR for volatility adjustment
    df = OHLCVRepository.get_recent_data(session, symbol, '1h', limit=20)
    df = TechnicalIndicators.add_volatility_indicators(df)
    atr = df['atr_14'].iloc[-1]

    # Calculate optimal position size
    position_size = enhanced_risk_manager.calculate_optimal_position_size(
        account_balance=account_balance,
        entry_price=current_price,
        stop_loss_price=stop_loss_price,
        confidence=signal['confidence'],
        atr=atr
    )

    log.info(f"📊 Position size: ${position_size:.2f} ({position_size/account_balance:.2%} of balance)")

    # Execute via executor
    trade = trading_executor.execute_signal(
        symbol=symbol,
        signal=signal,
        account_balance=account_balance
    )

    if trade:
        log.info(f"✅ Trade executed: ID={trade.id}")
    else:
        log.warning(f"⚠️  Trade execution failed")
```

---

### Phase 6: Position Monitoring

```python
def monitor_open_positions():
    """Monitor all open positions and close if TP/SL hit"""

    with db.session_scope() as session:
        open_trades = TradeRepository.get_open_trades(session)

        if not open_trades:
            return

        log.debug(f"📈 Monitoring {len(open_trades)} open position(s)")

        for trade in open_trades:
            try:
                monitor_single_position(trade, session)
            except Exception as e:
                log.error(f"Error monitoring trade {trade.id}: {e}")


def monitor_single_position(trade, session):
    """Monitor a single position"""

    # Get current price
    current_price = binance_client.get_price(trade.symbol)

    # Calculate unrealized P/L
    if trade.side == TradeSide.BUY:
        unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
    else:
        unrealized_pnl = (trade.entry_price - current_price) * trade.quantity

    unrealized_pnl_pct = (unrealized_pnl / (trade.entry_price * trade.quantity)) * 100

    log.debug(
        f"   {trade.symbol} | Entry: ${trade.entry_price:.2f} | "
        f"Current: ${current_price:.2f} | "
        f"Unrealized P/L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)"
    )

    # Check exit conditions (for paper trading)
    if trade.is_paper_trade:
        exit_reason = None

        if trade.side == TradeSide.BUY:
            if current_price <= trade.stop_loss:
                exit_reason = 'STOP_LOSS'
            elif current_price >= trade.take_profit:
                exit_reason = 'TAKE_PROFIT'
        else:  # SELL
            if current_price >= trade.stop_loss:
                exit_reason = 'STOP_LOSS'
            elif current_price <= trade.take_profit:
                exit_reason = 'TAKE_PROFIT'

        if exit_reason:
            close_trade(trade, current_price, exit_reason, session)

    else:
        # Live trading: check if OCO order filled
        order_status = binance_client.get_order_status(trade.oco_order_id)
        if order_status == 'FILLED':
            close_trade(trade, current_price, 'OCO_FILLED', session)
```

---

### Phase 7: Close Trade

```python
def close_trade(trade, exit_price, exit_reason, session):
    """Close a trade and calculate P/L"""

    log.info(f"🎯 Closing trade {trade.id} ({trade.symbol}) - Reason: {exit_reason}")

    # Update trade
    trade.exit_price = exit_price
    trade.exit_time = datetime.utcnow()
    trade.status = TradeStatus.CLOSED

    # Calculate duration
    duration = trade.exit_time - trade.entry_time
    trade.duration_minutes = duration.total_seconds() / 60

    # Calculate P/L
    if trade.side == TradeSide.BUY:
        gross_pnl = (exit_price - trade.entry_price) * trade.quantity
    else:
        gross_pnl = (trade.entry_price - exit_price) * trade.quantity

    # Subtract fees (0.1% per side = 0.2% total)
    entry_value = trade.entry_price * trade.quantity
    exit_value = exit_price * trade.quantity
    fees = (entry_value + exit_value) * 0.001

    net_pnl = gross_pnl - fees

    trade.gross_profit_loss = gross_pnl
    trade.fees_paid = fees
    trade.net_profit_loss = net_pnl
    trade.profit_loss_percent = (net_pnl / entry_value) * 100

    session.commit()

    # Log results
    log.info(
        f"✅ Trade closed | "
        f"Entry: ${trade.entry_price:.2f} | "
        f"Exit: ${exit_price:.2f} | "
        f"Duration: {duration} | "
        f"P/L: ${net_pnl:+.2f} ({trade.profit_loss_percent:+.2f}%)"
    )

    # Send notification
    telegram.send_trade_close(
        symbol=trade.symbol,
        exit_reason=exit_reason,
        pnl=net_pnl,
        pnl_pct=trade.profit_loss_percent
    )
```

---

## Error Handling

### Network Errors

```python
@retry(tries=3, delay=2, backoff=2)
def place_order(...):
    try:
        order = binance_client.create_market_order(...)
        return order
    except NetworkError as e:
        log.warning(f"Network error, retrying: {e}")
        raise  # Will retry
    except Exception as e:
        log.error(f"Order failed: {e}")
        telegram.send_error(f"Order placement failed: {e}")
        return None
```

### WebSocket Disconnection

```python
class WebSocketCollector:
    def _handle_error(self, error):
        log.error(f"WebSocket error: {error}")

        # Auto-reconnect after 5s
        time.sleep(5)
        self.start()

        log.info("WebSocket reconnected")
```

### Database Errors

```python
def session_scope(self):
    session = self.Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        session.close()
```

---

## Shutdown Procedure

```python
def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""

    log.info("\n⚠️  Shutdown signal received")
    log.info("Stopping bot gracefully...")

    # Stop WebSocket
    collector.stop()
    log.info("✅ WebSocket stopped")

    # Optionally close open positions
    if settings.trading.close_positions_on_shutdown:
        close_all_open_positions()

    # Final summary
    with db.session_scope() as session:
        summary = TradeRepository.get_performance_summary(session, days=1)
        log.info(f"📊 Today's summary: {summary['total_trades']} trades, P/L: ${summary['total_pnl']:.2f}")

    # Send notification
    telegram.send_message("🛑 Bot stopped")

    log.info("=" * 60)
    log.info("Bot shutdown complete. Goodbye!")
    log.info("=" * 60)

    sys.exit(0)


# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
```

---

## Performance Monitoring

### Periodic Reports

```python
# In main loop, every 100 iterations
if iteration % 100 == 0:
    with db.session_scope() as session:
        summary = TradeRepository.get_performance_summary(session, days=1)

        log.info("=" * 60)
        log.info(f"📊 DAILY PERFORMANCE REPORT")
        log.info(f"Total Trades: {summary['total_trades']}")
        log.info(f"Win Rate: {summary['win_rate']:.1%}")
        log.info(f"Total P/L: ${summary['total_pnl']:.2f}")
        log.info(f"Largest Win: ${summary['largest_win']:.2f}")
        log.info(f"Largest Loss: ${summary['largest_loss']:.2f}")
        log.info("=" * 60)

        # Send to Telegram
        telegram.send_daily_summary()
```

---

## Complete Example Scenario

**Scenario:** Bot detects and executes BUY signal

```
[14:00:00] WebSocket receives BTC/USDT candle: close $45,050
[14:00:01] Save to database
[14:00:10] Iteration 10 - Start analysis
[14:00:11] Load last 100 candles for BTC/USDT
[14:00:12] Calculate 50+ indicators
[14:00:13] ML predicts: UP (confidence: 0.75)
[14:00:14] Generate signals:
           - Technical: BUY (RSI oversold, MACD bullish)
           - Trend: BUY (Strong uptrend)
           - ML: BUY (confidence 0.75)
[14:00:15] Combined signal: BUY (confidence: 0.78)
[14:00:16] Check validations:
           ✅ Confidence > 0.70
           ✅ Open positions: 1/3
           ✅ No open BTC/USDT position
           ✅ Daily loss within limit
[14:00:17] Calculate position size:
           - Account: $10,000
           - Risk: 5%
           - Fractional Kelly: 3.3%
           - Final: $257.40 (2.57%)
[14:00:18] Execute: BUY 0.00572 BTC @ $45,050
[14:00:19] Save to database (Trade ID: 42)
[14:00:20] Send Telegram: "🤖 Trade executed..."
[14:00:21] Log: "✅ Trade executed: ID=42"

... Monitoring every 10s ...

[16:15:30] Current price: $45,450 (TP hit!)
[16:15:31] Close trade: ID=42
[16:15:32] Calculate P/L: +$2.29 (+0.89%)
[16:15:33] Send Telegram: "🎯 Trade closed: +$2.29"
[16:15:34] Log: "✅ Trade closed | P/L: +$2.29"
```

---

## Next Steps

**Đọc tiếp:**
- [6. GUI Architecture →](./06_gui_architecture.md) - Desktop app architecture
- [7. Deployment Guide →](./07_deployment.md) - Deployment instructions

**Back to:** [Index](./README.md)

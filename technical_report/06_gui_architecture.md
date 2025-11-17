# 6. GUI Architecture

## Overview

Desktop application built with **PyQt5** providing real-time monitoring and control.

**Key Features:**
- ⚡ Non-blocking UI (all data loading in background threads)
- 📊 Real-time updates (prices every 2s, positions every 5s)
- 🎨 Professional UI with color coding
- 📈 Interactive charts with pyqtgraph
- 💾 Trade history with CSV export

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────┐
│            main_gui.py (Entry Point)             │
│   • QApplication initialization                  │
│   • Splash screen                                │
│   • Create MainWindow                            │
└───────────────────┬──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│         MainWindow (QMainWindow)                 │
│   ┌──────────────────────────────────────┐      │
│   │          Header (QWidget)             │      │
│   │   • Title, System Time                │      │
│   └──────────────────────────────────────┘      │
│   ┌──────────────────────────────────────┐      │
│   │       Tab Widget (QTabWidget)         │      │
│   │  ┌────────────────────────────────┐   │      │
│   │  │  Tab 1: Dashboard              │   │      │
│   │  │    - PriceWidget               │   │      │
│   │  └────────────────────────────────┘   │      │
│   │  ┌────────────────────────────────┐   │      │
│   │  │  Tab 2: Trading Control        │   │      │
│   │  │    - TradingPanel              │   │      │
│   │  └────────────────────────────────┘   │      │
│   │  ┌────────────────────────────────┐   │      │
│   │  │  Tab 3: Live Monitoring        │   │      │
│   │  │    - MonitoringWidget          │   │      │
│   │  └────────────────────────────────┘   │      │
│   │  ┌────────────────────────────────┐   │      │
│   │  │  Tab 4: Trade History          │   │      │
│   │  │    - HistoryWidget             │   │      │
│   │  └────────────────────────────────┘   │      │
│   │  ┌────────────────────────────────┐   │      │
│   │  │  Tab 5: Charts                 │   │      │
│   │  │    - ChartWidget               │   │      │
│   │  └────────────────────────────────┘   │      │
│   └──────────────────────────────────────┘      │
│   ┌──────────────────────────────────────┐      │
│   │     Status Bar (QStatusBar)           │      │
│   │   • Database stats, Messages          │      │
│   └──────────────────────────────────────┘      │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│   Widgets    │    │ Background Workers│
│  (UI Logic)  │◄───┤   (QThread)      │
└──────────────┘    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
              ┌──────────┐      ┌──────────┐
              │ Database │      │ Binance  │
              │          │      │   API    │
              └──────────┘      └──────────┘
```

---

## Thread Architecture

### Main Thread (UI)
- Handles all UI rendering
- Event loop (user interactions)
- Updates widgets when signals received
- **NEVER** performs blocking operations

### Worker Threads (QThread)
- All data loading happens here
- Communicates via Qt Signals/Slots
- Non-blocking, runs concurrently

```
┌─────────────────┐
│   Main Thread   │  (UI Event Loop)
│   (PyQt5)       │
└────────┬────────┘
         │
         │ Signals/Slots
         │
    ┌────┴────┬────────┬────────┬────────┬────────┐
    │         │        │        │        │        │
    ▼         ▼        ▼        ▼        ▼        ▼
┌──────┐ ┌───────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Price │ │ Pos.  │ │ Perf.│ │ Chart│ │History│ │ Stats│
│Worker│ │Worker │ │Worker│ │Worker│ │Worker │ │Worker│
└──┬───┘ └───┬───┘ └───┬──┘ └───┬──┘ └───┬───┘ └───┬──┘
   │         │         │        │        │         │
   └─────────┴─────────┴────────┴────────┴─────────┘
                       │
                  ┌────┴────┐
                  ▼         ▼
           ┌──────────┐ ┌──────────┐
           │ Database │ │ Binance  │
           └──────────┘ └──────────┘
```

---

## Core Components

### 1. MainWindow (`src/gui/main_window.py`)

**Responsibility:** Application shell, orchestrates everything

**Key Methods:**

```python
class MainWindow(QMainWindow):
    def __init__(self):
        self.init_ui()  # Create UI
        self.init_database()  # Initialize DB
        self.start_background_workers()  # Start threads

    def init_ui(self):
        # Create header
        # Create tab widget
        # Add all tabs
        # Create menu bar
        # Create status bar
        # Connect signals

    def start_background_workers(self):
        # Create and start all QThread workers
        self.price_worker = PriceUpdateWorker(...)
        self.price_worker.price_updated.connect(...)
        self.price_worker.start()
        # ... other workers

    def closeEvent(self, event):
        # Stop all workers before closing
        for worker in self.workers:
            worker.stop()
            worker.wait()
```

---

### 2. Background Workers (`src/gui/workers.py`)

#### Base Pattern

```python
class BaseWorker(QThread):
    # Define signals
    data_updated = pyqtSignal(object)  # Emits data
    error_occurred = pyqtSignal(str)   # Emits errors

    def __init__(self, interval=10):
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        """Main worker loop - runs in background"""
        while self.running:
            try:
                # 1. Fetch data (blocking operation)
                data = fetch_data_from_db_or_api()

                # 2. Emit signal to main thread
                self.data_updated.emit(data)

                # 3. Sleep
                time.sleep(self.interval)

            except Exception as e:
                self.error_occurred.emit(str(e))

    def stop(self):
        """Stop worker gracefully"""
        self.running = False
        self.wait()  # Wait for thread to finish
```

#### PriceUpdateWorker

```python
class PriceUpdateWorker(QThread):
    price_updated = pyqtSignal(dict)  # {symbol: {price, change, volume, ...}}

    def run(self):
        while self.running:
            prices = {}
            for symbol in self.symbols:
                price = binance_client.get_price(symbol)
                ticker = binance_client.get_ticker(symbol)
                prices[symbol] = {
                    'price': price,
                    'change_24h': float(ticker['priceChangePercent']),
                    'volume_24h': float(ticker['volume']),
                    'high_24h': float(ticker['highPrice']),
                    'low_24h': float(ticker['lowPrice'])
                }

            # Emit to main thread
            self.price_updated.emit(prices)

            time.sleep(2)  # Update every 2s
```

#### OpenPositionsWorker

```python
class OpenPositionsWorker(QThread):
    positions_updated = pyqtSignal(list)  # [{trade_info, unrealized_pnl, ...}]

    def run(self):
        while self.running:
            with db.session_scope() as session:
                trades = TradeRepository.get_open_trades(session)

                position_list = []
                for trade in trades:
                    current_price = binance_client.get_price(trade.symbol)

                    # Calculate unrealized P/L
                    if trade.side.value == 'BUY':
                        unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                    else:
                        unrealized_pnl = (trade.entry_price - current_price) * trade.quantity

                    position_list.append({
                        'id': trade.id,
                        'symbol': trade.symbol,
                        'side': trade.side.value,
                        'entry_price': trade.entry_price,
                        'current_price': current_price,
                        'unrealized_pnl': unrealized_pnl,
                        ...
                    })

                self.positions_updated.emit(position_list)

            time.sleep(5)  # Update every 5s
```

---

### 3. Widgets (`src/gui/widgets/`)

#### PriceWidget (`price_widget.py`)

**Purpose:** Display real-time prices in table

**UI Elements:**
- QLabel (title)
- QTableWidget (prices)
- QLabel (status)

**Key Method:**

```python
@pyqtSlot(dict)
def update_prices(self, prices: Dict):
    """
    Slot connected to PriceUpdateWorker.price_updated signal

    Args:
        prices: {symbol: {price, change_24h, volume_24h, ...}}
    """
    self.table.setRowCount(len(prices))

    row = 0
    for symbol, data in prices.items():
        # Symbol
        symbol_item = QTableWidgetItem(symbol)
        self.table.setItem(row, 0, symbol_item)

        # Price
        price_item = QTableWidgetItem(f"${data['price']:,.2f}")
        price_item.setFont(QFont("Arial", 12, QFont.Bold))

        # Color based on change
        if old_price < new_price:
            price_item.setForeground(QColor("#27ae60"))  # Green
        elif old_price > new_price:
            price_item.setForeground(QColor("#e74c3c"))  # Red

        self.table.setItem(row, 1, price_item)

        # ... other columns

        row += 1

    # Update status
    self.status_label.setText(f"✅ Last updated: {current_time()}")
```

---

#### TradingPanel (`trading_panel.py`)

**Purpose:** Control bot (start/stop, manual trade)

**UI Elements:**
- Status indicators (Running/Stopped)
- Mode selector (Paper/Live)
- Start/Stop buttons
- Manual trade form
- Activity log (QTextEdit)

**Signals Emitted:**
```python
start_bot_signal = pyqtSignal(str)  # mode: "paper" or "live"
stop_bot_signal = pyqtSignal()
manual_trade_signal = pyqtSignal(dict)  # trade params
```

**Slots:**
```python
def _on_start_clicked(self):
    mode = "paper" if "Paper" in self.mode_combo.currentText() else "live"

    if mode == "live":
        # Show confirmation dialog
        reply = QMessageBox.question(...)
        if reply == QMessageBox.No:
            return

    # Emit signal
    self.start_bot_signal.emit(mode)

    # Update UI
    self.status_label.setText("🟢 RUNNING")
    self.start_button.setEnabled(False)
    self.stop_button.setEnabled(True)
```

---

#### ChartWidget (`chart_widget.py`)

**Purpose:** Display interactive candlestick charts

**Technology:** pyqtgraph (10-100x faster than matplotlib)

**Key Components:**

```python
def init_ui(self):
    # Create GraphicsLayoutWidget
    self.graphics_widget = pg.GraphicsLayoutWidget()

    # Price plot (candlestick)
    self.price_plot = self.graphics_widget.addPlot(row=0, col=0)
    self.candlestick_item = pg.CandlestickItem()
    self.price_plot.addItem(self.candlestick_item)

    # Volume plot
    self.volume_plot = self.graphics_widget.addPlot(row=1, col=0)
    self.volume_bars = pg.BarGraphItem()
    self.volume_plot.addItem(self.volume_bars)

    # Link axes
    self.volume_plot.setXLink(self.price_plot)
```

**Update Method:**

```python
@pyqtSlot(object)
def update_chart(self, df):
    """
    Update chart with OHLCV data

    Args:
        df: pandas DataFrame with columns: timestamp, open, high, low, close, volume
    """
    # Prepare candlestick data
    candlestick_data = []
    for i, (timestamp, row) in enumerate(df.iterrows()):
        candlestick_data.append({
            'time': i,
            'open': row['open'],
            'close': row['close'],
            'min': row['low'],
            'max': row['high']
        })

    # Update candlestick
    self.candlestick_item.setData(candlestick_data)

    # Update volume bars
    volumes = df['volume'].values
    volume_colors = [
        (0, 255, 0, 150) if row['close'] >= row['open'] else (255, 0, 0, 150)
        for _, row in df.iterrows()
    ]

    self.volume_bars.setOpts(
        x=range(len(df)),
        height=volumes,
        brushes=volume_colors
    )

    # Auto-range
    self.price_plot.enableAutoRange()
```

---

## Signal/Slot Communication

**Pattern:**

```
Worker Thread                    Main Thread (UI)
     │                                │
     │  1. Fetch data                 │
     │     (blocking)                 │
     │                                │
     │  2. Emit signal                │
     ├───────────────────────────────>│
     │   price_updated.emit(data)     │
     │                                │
     │                       3. Slot triggered
     │                       update_prices(data)
     │                                │
     │                       4. Update UI
     │                       (non-blocking)
     │                                │
     │  5. Sleep                      │
     │                                │
     │  ... repeat ...                │
```

**Code:**

```python
# In MainWindow.__init__()

# Create worker
self.price_worker = PriceUpdateWorker(symbols, interval=2)

# Connect signal to slot
self.price_worker.price_updated.connect(self.price_widget.update_prices)

# Connect error signal
self.price_worker.error_occurred.connect(self._on_worker_error)

# Start worker
self.price_worker.start()


# In PriceWidget
@pyqtSlot(dict)
def update_prices(self, prices):
    # This runs in main thread
    # Update UI safely
    ...
```

---

## Performance Optimizations

### 1. Non-Blocking Operations

**❌ Bad (blocks UI):**
```python
def refresh_data(self):
    # This freezes the UI for 2s!
    data = load_from_database()  # 2s blocking call
    self.update_table(data)
```

**✅ Good (non-blocking):**
```python
def refresh_data(self):
    # Start worker to load data
    worker = DataLoadWorker()
    worker.data_loaded.connect(self.update_table)
    worker.start()

# UI remains responsive!
```

### 2. Fast Charts

**pyqtgraph vs matplotlib:**
- pyqtgraph: **10-100x faster**
- Handles real-time updates smoothly
- Can plot thousands of points

### 3. Efficient Updates

**Only update changed data:**

```python
def update_prices(self, new_prices):
    for row, (symbol, data) in enumerate(new_prices.items()):
        # Only update if price changed
        old_price = self.price_cache.get(symbol, {}).get('price', 0)
        new_price = data['price']

        if old_price != new_price:
            # Update table cell
            self.table.item(row, 1).setText(f"${new_price:,.2f}")

            # Animate color
            if new_price > old_price:
                self.table.item(row, 1).setForeground(QColor("#27ae60"))

    # Cache for next update
    self.price_cache = new_prices
```

### 4. Lazy Loading

**Load data only when needed:**

```python
def on_tab_changed(self, index):
    """Load data when tab is activated"""

    if index == TAB_CHARTS and not self.chart_loaded:
        # Load chart data
        self._load_chart_data()
        self.chart_loaded = True
```

---

## Styling

### Custom CSS (QSS)

```python
self.setStyleSheet("""
    QWidget {
        font-family: Arial;
        font-size: 10pt;
    }

    QTableWidget {
        background-color: #f8f9fa;
        alternate-background-color: #e9ecef;
        gridline-color: #dee2e6;
    }

    QHeaderView::section {
        background-color: #343a40;
        color: white;
        padding: 8px;
        font-weight: bold;
    }

    QPushButton {
        background-color: #28a745;
        color: white;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
    }

    QPushButton:hover {
        background-color: #218838;
    }

    QPushButton:pressed {
        background-color: #1e7e34;
    }

    QPushButton:disabled {
        background-color: #6c757d;
    }
""")
```

---

## Error Handling

### Worker Errors

```python
class SomeWorker(QThread):
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            data = fetch_data()
            self.data_loaded.emit(data)
        except Exception as e:
            # Emit error signal
            self.error_occurred.emit(str(e))
            log.error(f"Worker error: {e}")


# In MainWindow
def _on_worker_error(self, error: str):
    # Show to user
    self.statusBar.showMessage(f"⚠️ Error: {error}", 5000)

    # Log
    log.error(f"Worker error: {error}")
```

### UI Validation

```python
def _on_manual_trade_clicked(self):
    # Validate inputs
    quantity = self.quantity_spin.value()
    if quantity <= 0:
        QMessageBox.warning(self, "Invalid Input", "Quantity must be > 0")
        return

    # Confirm
    reply = QMessageBox.question(
        self,
        "Confirm Trade",
        f"Execute {side} {quantity} {symbol}?",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        self.manual_trade_signal.emit(trade_params)
```

---

## Next Steps

**Đọc tiếp:**
- [7. Deployment Guide →](./07_deployment.md) - Production deployment

**Back to:** [Index](./README.md)

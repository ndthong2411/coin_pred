"""
WebSocket collector for real-time market data from Binance.
"""
import json
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional
from binance.streams import ThreadedWebsocketManager
from config import settings
from src.utils import log
from src.database import db, OHLCV, OHLCVRepository


class BinanceWebSocket:
    """Real-time data collector using Binance WebSocket."""

    def __init__(self, symbols: List[str] = None, testnet: bool = None):
        """
        Initialize WebSocket collector.

        Args:
            symbols: List of symbols to subscribe
            testnet: Use testnet (default from settings)
        """
        self.symbols = symbols or settings.trading.target_symbols
        self.testnet = testnet if testnet is not None else settings.binance.testnet
        self.ws_manager = None
        self.is_running = False
        self.callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

        # Data buffers
        self.latest_prices: Dict[str, float] = {}
        self.latest_klines: Dict[str, Dict] = {}

    def start(self):
        """Start WebSocket streams."""
        if self.is_running:
            log.warning("WebSocket already running")
            return

        log.info(f"Starting WebSocket for symbols: {self.symbols}")

        # Initialize WebSocket manager
        api_key = settings.binance.api_key if not self.testnet else None
        api_secret = settings.binance.api_secret if not self.testnet else None

        self.ws_manager = ThreadedWebsocketManager(
            api_key=api_key,
            api_secret=api_secret,
            testnet=self.testnet
        )
        self.ws_manager.start()

        # Subscribe to streams for each symbol
        for symbol in self.symbols:
            self._subscribe_symbol(symbol)

        self.is_running = True
        log.info("WebSocket streams started")

    def stop(self):
        """Stop WebSocket streams."""
        if not self.is_running:
            return

        log.info("Stopping WebSocket streams")
        if self.ws_manager:
            self.ws_manager.stop()
        self.is_running = False
        log.info("WebSocket streams stopped")

    def _subscribe_symbol(self, symbol: str):
        """Subscribe to streams for a symbol."""
        from src.utils import denormalize_symbol

        symbol_lower = denormalize_symbol(symbol).lower()

        # Subscribe to trade stream (real-time prices)
        self.ws_manager.start_trade_socket(
            callback=self._handle_trade_message,
            symbol=symbol_lower
        )

        # Subscribe to kline stream (candlesticks)
        self.ws_manager.start_kline_socket(
            callback=self._handle_kline_message,
            symbol=symbol_lower,
            interval='1m'
        )

        log.debug(f"Subscribed to streams for {symbol}")

    def _handle_trade_message(self, msg):
        """Handle trade stream messages."""
        if msg['e'] == 'error':
            log.error(f"WebSocket error: {msg}")
            return

        if msg['e'] != 'trade':
            return

        symbol = msg['s']
        price = float(msg['p'])
        quantity = float(msg['q'])
        timestamp = datetime.fromtimestamp(msg['T'] / 1000)

        # Update latest price
        with self._lock:
            self.latest_prices[symbol] = price

        # Trigger callbacks
        self._trigger_callbacks('trade', {
            'symbol': symbol,
            'price': price,
            'quantity': quantity,
            'timestamp': timestamp
        })

    def _handle_kline_message(self, msg):
        """Handle kline stream messages."""
        if msg['e'] == 'error':
            log.error(f"WebSocket error: {msg}")
            return

        if msg['e'] != 'kline':
            return

        kline = msg['k']
        symbol = kline['s']
        is_closed = kline['x']  # Is this kline closed?

        kline_data = {
            'symbol': symbol,
            'timestamp': datetime.fromtimestamp(kline['t'] / 1000),
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c']),
            'volume': float(kline['v']),
            'is_closed': is_closed
        }

        # Update latest kline
        with self._lock:
            self.latest_klines[symbol] = kline_data

        # Only save to database when kline is closed
        if is_closed:
            self._save_kline(kline_data)

        # Trigger callbacks
        self._trigger_callbacks('kline', kline_data)

    def _save_kline(self, kline_data: Dict):
        """Save completed kline to database."""
        try:
            with db.session_scope() as session:
                OHLCVRepository.create(
                    session,
                    symbol=kline_data['symbol'],
                    timeframe='1m',
                    timestamp=kline_data['timestamp'],
                    open=kline_data['open'],
                    high=kline_data['high'],
                    low=kline_data['low'],
                    close=kline_data['close'],
                    volume=kline_data['volume']
                )
            log.debug(f"Saved kline: {kline_data['symbol']} {kline_data['timestamp']}")
        except Exception as e:
            log.error(f"Error saving kline: {e}")

    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for WebSocket events.

        Args:
            event_type: 'trade' or 'kline'
            callback: Function to call when event occurs
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        log.debug(f"Registered callback for {event_type}")

    def _trigger_callbacks(self, event_type: str, data: Dict):
        """Trigger all callbacks for an event type."""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    log.error(f"Callback error: {e}")

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol."""
        with self._lock:
            return self.latest_prices.get(symbol)

    def get_latest_kline(self, symbol: str) -> Optional[Dict]:
        """Get latest kline for a symbol."""
        with self._lock:
            return self.latest_klines.get(symbol)

    def get_all_latest_prices(self) -> Dict[str, float]:
        """Get all latest prices."""
        with self._lock:
            return self.latest_prices.copy()


# Global WebSocket instance
ws_collector = BinanceWebSocket()


if __name__ == "__main__":
    # Test WebSocket collector
    print("Testing WebSocket collector...")

    # Define callbacks
    def on_trade(data):
        print(f"Trade: {data['symbol']} @ ${data['price']:,.2f}")

    def on_kline(data):
        status = "CLOSED" if data['is_closed'] else "UPDATING"
        print(f"Kline [{status}]: {data['symbol']} C:{data['close']:.2f}")

    # Register callbacks
    ws_collector.register_callback('trade', on_trade)
    ws_collector.register_callback('kline', on_kline)

    # Start collecting
    ws_collector.start()

    try:
        print("\nCollecting data for 30 seconds...")
        time.sleep(30)

        print("\nLatest prices:")
        prices = ws_collector.get_all_latest_prices()
        for symbol, price in prices.items():
            print(f"  {symbol}: ${price:,.2f}")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        ws_collector.stop()

    print("✅ WebSocket test complete")

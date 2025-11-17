"""
Background workers for non-blocking real-time updates.
Uses QThread to prevent UI freezing.
"""
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, List, Optional
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_collection import binance_client
from src.database import db, TradeRepository, OHLCVRepository
from src.utils import log


class PriceUpdateWorker(QThread):
    """Worker thread for real-time price updates."""

    price_updated = pyqtSignal(dict)  # Signal emits {symbol: price}
    error_occurred = pyqtSignal(str)

    def __init__(self, symbols: List[str], interval: int = 2):
        """
        Initialize price update worker.

        Args:
            symbols: List of symbols to monitor
            interval: Update interval in seconds
        """
        super().__init__()
        self.symbols = symbols
        self.interval = interval
        self.running = True

    def run(self):
        """Main worker loop - runs in background thread."""
        while self.running:
            try:
                prices = {}
                for symbol in self.symbols:
                    try:
                        price = binance_client.get_price(symbol)
                        ticker = binance_client.get_ticker(symbol)
                        prices[symbol] = {
                            'price': price,
                            'change_24h': float(ticker.get('priceChangePercent', 0)),
                            'volume_24h': float(ticker.get('volume', 0)),
                            'high_24h': float(ticker.get('highPrice', 0)),
                            'low_24h': float(ticker.get('lowPrice', 0))
                        }
                    except Exception as e:
                        log.error(f"Error fetching {symbol}: {e}")
                        prices[symbol] = None

                # Emit signal with prices
                self.price_updated.emit(prices)

                # Sleep interval
                time.sleep(self.interval)

            except Exception as e:
                self.error_occurred.emit(str(e))
                time.sleep(self.interval)

    def stop(self):
        """Stop the worker."""
        self.running = False
        self.wait()


class TradeHistoryWorker(QThread):
    """Worker thread for loading trade history."""

    trades_loaded = pyqtSignal(list)  # Signal emits list of trades
    error_occurred = pyqtSignal(str)

    def __init__(self, symbol: Optional[str] = None, days: int = 30):
        """
        Initialize trade history worker.

        Args:
            symbol: Filter by symbol (optional)
            days: Number of days to load
        """
        super().__init__()
        self.symbol = symbol
        self.days = days

    def run(self):
        """Load trades from database."""
        try:
            with db.session_scope() as session:
                trades = TradeRepository.get_closed_trades(
                    session,
                    symbol=self.symbol,
                    days=self.days
                )

                trade_list = []
                for trade in trades:
                    trade_list.append({
                        'id': trade.id,
                        'symbol': trade.symbol,
                        'side': trade.side.value,
                        'entry_price': trade.entry_price,
                        'exit_price': trade.exit_price,
                        'quantity': trade.quantity,
                        'status': trade.status.value,
                        'profit_loss': trade.net_profit_loss,
                        'profit_loss_percent': trade.profit_loss_percent,
                        'entry_time': trade.entry_time,
                        'exit_time': trade.exit_time,
                        'confidence': trade.confidence_score
                    })

                self.trades_loaded.emit(trade_list)

        except Exception as e:
            self.error_occurred.emit(str(e))


class PerformanceWorker(QThread):
    """Worker thread for loading performance metrics."""

    metrics_loaded = pyqtSignal(dict)  # Signal emits performance dict
    error_occurred = pyqtSignal(str)

    def __init__(self, days: int = 30):
        """
        Initialize performance worker.

        Args:
            days: Number of days to analyze
        """
        super().__init__()
        self.days = days

    def run(self):
        """Load performance metrics from database."""
        try:
            with db.session_scope() as session:
                summary = TradeRepository.get_performance_summary(session, days=self.days)
                self.metrics_loaded.emit(summary)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChartDataWorker(QThread):
    """Worker thread for loading chart data."""

    data_loaded = pyqtSignal(object)  # Signal emits pandas DataFrame
    error_occurred = pyqtSignal(str)

    def __init__(self, symbol: str, timeframe: str = "1h", limit: int = 100):
        """
        Initialize chart data worker.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles
        """
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit

    def run(self):
        """Load OHLCV data."""
        try:
            df = binance_client.get_historical_klines(
                self.symbol,
                self.timeframe,
                limit=self.limit
            )
            self.data_loaded.emit(df)
        except Exception as e:
            self.error_occurred.emit(str(e))


class OpenPositionsWorker(QThread):
    """Worker thread for monitoring open positions."""

    positions_updated = pyqtSignal(list)  # Signal emits list of open trades
    error_occurred = pyqtSignal(str)

    def __init__(self, interval: int = 5):
        """
        Initialize open positions worker.

        Args:
            interval: Update interval in seconds
        """
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        """Monitor open positions."""
        while self.running:
            try:
                with db.session_scope() as session:
                    trades = TradeRepository.get_open_trades(session)

                    position_list = []
                    for trade in trades:
                        # Get current price for unrealized P/L
                        try:
                            current_price = binance_client.get_price(trade.symbol)

                            # Calculate unrealized P/L
                            if trade.side.value == "BUY":
                                unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                            else:
                                unrealized_pnl = (trade.entry_price - current_price) * trade.quantity

                            unrealized_pnl_percent = (unrealized_pnl / (trade.entry_price * trade.quantity)) * 100

                        except:
                            current_price = trade.entry_price
                            unrealized_pnl = 0
                            unrealized_pnl_percent = 0

                        position_list.append({
                            'id': trade.id,
                            'symbol': trade.symbol,
                            'side': trade.side.value,
                            'entry_price': trade.entry_price,
                            'current_price': current_price,
                            'quantity': trade.quantity,
                            'unrealized_pnl': unrealized_pnl,
                            'unrealized_pnl_percent': unrealized_pnl_percent,
                            'stop_loss': trade.stop_loss,
                            'take_profit': trade.take_profit,
                            'entry_time': trade.entry_time
                        })

                    self.positions_updated.emit(position_list)

                time.sleep(self.interval)

            except Exception as e:
                self.error_occurred.emit(str(e))
                time.sleep(self.interval)

    def stop(self):
        """Stop the worker."""
        self.running = False
        self.wait()


class SystemStatsWorker(QThread):
    """Worker thread for system statistics."""

    stats_updated = pyqtSignal(dict)  # Signal emits system stats
    error_occurred = pyqtSignal(str)

    def __init__(self, interval: int = 10):
        """
        Initialize system stats worker.

        Args:
            interval: Update interval in seconds
        """
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        """Monitor system stats."""
        while self.running:
            try:
                with db.session_scope() as session:
                    stats = {
                        'ohlcv_records': db.get_table_count('ohlcv'),
                        'total_trades': db.get_table_count('trades'),
                        'predictions': db.get_table_count('predictions'),
                        'features': db.get_table_count('features'),
                        'open_positions': len(TradeRepository.get_open_trades(session)),
                    }

                    self.stats_updated.emit(stats)

                time.sleep(self.interval)

            except Exception as e:
                self.error_occurred.emit(str(e))
                time.sleep(self.interval)

    def stop(self):
        """Stop the worker."""
        self.running = False
        self.wait()

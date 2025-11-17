"""
Enhanced main entry point with full trading capabilities.
"""
import sys
import argparse
import signal
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from src.utils import log
from src.utils.telegram_bot import telegram
from src.database import init_database, db, OHLCVRepository
from src.data_collection import binance_client, ws_collector
from src.feature_engineering import calculate_indicators_for_symbol
from src.trading import set_trading_executor, signal_generator, trading_executor


class EnhancedTradingBot:
    """Enhanced trading bot with full trading capabilities."""

    def __init__(self, mode: str = "paper"):
        """
        Initialize trading bot.

        Args:
            mode: Trading mode ('paper' or 'live')
        """
        self.mode = mode
        self.is_running = False
        self.account_balance = 10000.0  # Will be updated from Binance
        self._setup_signal_handlers()

        # Set trading executor
        set_trading_executor(mode)

        log.info(f"=" * 60)
        log.info(f"CRYPTO TRADING BOT - {mode.upper()} MODE")
        log.info(f"=" * 60)

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        log.warning(f"\nReceived signal {signum}. Shutting down...")
        self.stop()
        sys.exit(0)

    def initialize(self) -> bool:
        """
        Initialize all bot components.

        Returns:
            True if successful
        """
        log.info("\n📋 Initializing bot components...")

        # 1. Check configuration
        log.info("1️⃣  Checking configuration...")
        missing = settings.validate_required_keys()
        if missing and self.mode == "live":
            log.error(f"Missing required configuration: {missing}")
            return False
        log.info("✅ Configuration OK")

        # 2. Initialize database
        log.info("2️⃣  Initializing database...")
        try:
            init_database()
            if not db.check_connection():
                log.error("Database connection failed")
                return False
            log.info("✅ Database OK")
        except Exception as e:
            log.error(f"Database initialization failed: {e}")
            return False

        # 3. Test Binance API
        log.info("3️⃣  Testing Binance API connection...")
        try:
            if not binance_client.ping():
                log.error("Binance API connection failed")
                return False
            price = binance_client.get_price("BTC/USDT")
            log.info(f"✅ Binance API OK (BTC/USDT: ${price:,.2f})")
        except Exception as e:
            log.error(f"Binance API test failed: {e}")
            return False

        # 4. Check account balance
        if self.mode == "live":
            log.info("4️⃣  Checking account balance...")
            try:
                balances = binance_client.get_account_balance()
                self.account_balance = balances.get('USDT', {}).get('free', 0)
                log.info(f"✅ Account balance: {self.account_balance:.2f} USDT")

                if self.account_balance < 10:
                    log.warning("⚠️  Low account balance!")
            except Exception as e:
                log.error(f"Failed to get account balance: {e}")
                return False
        else:
            log.info(f"4️⃣  Paper trading balance: ${self.account_balance:,.2f}")

        log.info("\n✅ All systems initialized successfully!")
        log.info(settings.get_summary())

        # Send startup notification
        telegram.send_startup_message()

        return True

    def start(self):
        """Start the trading bot."""
        if not self.initialize():
            log.error("❌ Initialization failed. Exiting.")
            return

        self.is_running = True
        log.info("\n🚀 Starting trading bot...")
        log.info(f"Mode: {self.mode.upper()}")
        log.info(f"Symbols: {', '.join(settings.trading.target_symbols)}")

        # Start WebSocket for real-time data
        log.info("\n📡 Starting real-time data collection...")
        ws_collector.start()

        # Main trading loop
        try:
            self._run_trading_loop()
        except KeyboardInterrupt:
            log.info("\n⚠️  Interrupted by user")
        except Exception as e:
            log.error(f"\n❌ Fatal error: {e}")
            log.exception(e)
            telegram.send_error(str(e), "Fatal error in main loop")
        finally:
            self.stop()

    def _run_trading_loop(self):
        """Main trading loop with full trading logic."""
        log.info("\n🔄 Entering main trading loop...")
        log.info("Press Ctrl+C to stop\n")

        iteration = 0
        last_heartbeat = datetime.utcnow()

        while self.is_running:
            iteration += 1

            try:
                # Heartbeat every 5 minutes
                if (datetime.utcnow() - last_heartbeat).seconds > 300:
                    telegram.send_heartbeat()
                    last_heartbeat = datetime.utcnow()

                # Process each symbol
                for symbol in settings.trading.target_symbols:
                    try:
                        self._process_symbol(symbol, iteration)
                    except Exception as e:
                        log.error(f"Error processing {symbol}: {e}")

                # Check and close positions
                if trading_executor:
                    trading_executor.check_and_close_positions()

                # Sleep before next iteration
                time.sleep(settings.system.data_update_interval)

            except Exception as e:
                log.error(f"Error in trading loop: {e}")
                time.sleep(5)

    def _process_symbol(self, symbol: str, iteration: int):
        """Process a single symbol."""
        # Get latest price
        latest_price = ws_collector.get_latest_price(symbol)

        if not latest_price:
            log.debug(f"Waiting for price data for {symbol}...")
            return

        # Every 10 iterations, analyze and potentially trade
        if iteration % 10 == 0:
            log.info(f"\n--- Analyzing {symbol} @ {datetime.now().strftime('%H:%M:%S')} ---")
            log.info(f"Current Price: ${latest_price:,.2f}")

            # Get historical data from database
            with db.session_scope() as session:
                ohlcv_data = OHLCVRepository.get_latest(session, symbol, '1m', limit=200)

                if len(ohlcv_data) < 100:
                    log.warning(f"Insufficient data for {symbol} ({len(ohlcv_data)} candles)")
                    return

                # Convert to DataFrame
                df = OHLCVRepository.to_dataframe(ohlcv_data)

            # Calculate indicators
            df = calculate_indicators_for_symbol(df)

            if df.empty:
                log.warning(f"No data after indicator calculation for {symbol}")
                return

            # Generate signal
            signal = signal_generator.generate_signal(df, predictions=None)

            log.info(f"Signal: {signal['action']} (confidence: {signal['confidence']:.1%})")

            if signal['reasons']:
                log.info(f"Reasons: {', '.join(signal['reasons'][:3])}")

            # Execute signal if not HOLD
            if signal['action'] != "HOLD" and trading_executor:
                trade = trading_executor.execute_signal(symbol, signal, self.account_balance)

                if trade:
                    log.info(f"✅ Trade executed: {trade.id}")

                    # Send signal notification
                    telegram.send_trade_signal(
                        symbol=symbol,
                        action=signal['action'],
                        price=latest_price,
                        confidence=signal['confidence'],
                        reason=', '.join(signal['reasons'][:2])
                    )

    def stop(self):
        """Stop the trading bot."""
        if not self.is_running:
            return

        log.info("\n🛑 Stopping trading bot...")

        # Stop WebSocket
        log.info("Stopping WebSocket...")
        ws_collector.stop()

        # Close all open positions (if configured)
        # TODO: Implement emergency close all

        self.is_running = False

        # Send shutdown notification
        telegram.send_shutdown_message()

        log.info("✅ Bot stopped successfully")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Crypto Trading Bot')
    parser.add_argument(
        '--mode',
        type=str,
        choices=['paper', 'live'],
        default='paper',
        help='Trading mode (paper or live)'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated symbols to trade (overrides config)'
    )

    args = parser.parse_args()

    # Override symbols if provided
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        settings.trading.target_symbols = symbols

    # Safety check for live mode
    if args.mode == 'live':
        print("\n" + "⚠️ " * 20)
        print("WARNING: YOU ARE ABOUT TO START LIVE TRADING!")
        print("This will use REAL MONEY on your Binance account.")
        print("⚠️ " * 20)
        response = input("\nType 'YES I UNDERSTAND' to continue: ")
        if response != 'YES I UNDERSTAND':
            print("❌ Live trading cancelled")
            return 1

    # Start bot
    bot = EnhancedTradingBot(mode=args.mode)
    bot.start()

    return 0


if __name__ == "__main__":
    sys.exit(main())

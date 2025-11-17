"""
Main entry point for the Crypto Trading Bot.
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
from src.database import init_database, db
from src.data_collection import binance_client, ws_collector


class TradingBot:
    """Main trading bot application."""

    def __init__(self, mode: str = "paper"):
        """
        Initialize trading bot.

        Args:
            mode: Trading mode ('paper' or 'live')
        """
        self.mode = mode
        self.is_running = False
        self._setup_signal_handlers()

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

        # 4. Check account balance (if live mode)
        if self.mode == "live":
            log.info("4️⃣  Checking account balance...")
            try:
                balances = binance_client.get_account_balance()
                usdt_balance = balances.get('USDT', {}).get('free', 0)
                log.info(f"✅ Account balance: {usdt_balance:.2f} USDT")

                if usdt_balance < 10:
                    log.warning("⚠️  Low account balance!")
            except Exception as e:
                log.error(f"Failed to get account balance: {e}")
                return False

        log.info("\n✅ All systems initialized successfully!")
        log.info(settings.get_summary())

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
        finally:
            self.stop()

    def _run_trading_loop(self):
        """Main trading loop."""
        log.info("\n🔄 Entering main trading loop...")
        log.info("Press Ctrl+C to stop\n")

        iteration = 0

        while self.is_running:
            iteration += 1

            try:
                # Get latest prices
                prices = ws_collector.get_all_latest_prices()

                if prices:
                    log.info(f"\n--- Iteration {iteration} @ {datetime.now().strftime('%H:%M:%S')} ---")
                    for symbol, price in prices.items():
                        log.info(f"{symbol}: ${price:,.2f}")

                    # TODO: Add your trading logic here:
                    # 1. Calculate indicators
                    # 2. Get predictions from models
                    # 3. Generate signals
                    # 4. Execute trades (if confidence > threshold)
                    # 5. Monitor open positions
                    # 6. Apply risk management

                else:
                    log.debug("Waiting for price data...")

                # Sleep before next iteration
                time.sleep(settings.system.data_update_interval)

            except Exception as e:
                log.error(f"Error in trading loop: {e}")
                time.sleep(5)

    def stop(self):
        """Stop the trading bot."""
        if not self.is_running:
            return

        log.info("\n🛑 Stopping trading bot...")

        # Stop WebSocket
        log.info("Stopping WebSocket...")
        ws_collector.stop()

        # TODO: Close all open positions (if any)

        self.is_running = False
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
    bot = TradingBot(mode=args.mode)
    bot.start()

    return 0


if __name__ == "__main__":
    sys.exit(main())

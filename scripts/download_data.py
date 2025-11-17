"""
Download historical data for all target symbols.
"""
import sys
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_collection import historical_downloader
from src.database import init_database
from config import settings
from src.utils import log


def main():
    """Download historical data."""
    parser = argparse.ArgumentParser(description='Download historical cryptocurrency data')
    parser.add_argument('--symbols', type=str, help='Comma-separated symbols (default from config)')
    parser.add_argument('--interval', type=str, default='1m', help='Timeframe (1m, 5m, 15m, 1h)')
    parser.add_argument('--days', type=int, default=30, help='Days to download (default: 30)')

    args = parser.parse_args()

    print("=" * 60)
    print("HISTORICAL DATA DOWNLOADER")
    print("=" * 60)

    # Parse symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        symbols = settings.trading.target_symbols

    print(f"\nSymbols: {', '.join(symbols)}")
    print(f"Interval: {args.interval}")
    print(f"Days: {args.days}")

    # Initialize database
    print("\nInitializing database...")
    try:
        init_database()
        print("✅ Database ready")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return 1

    # Download data
    print(f"\nDownloading data for {len(symbols)} symbols...")
    print("-" * 60)

    try:
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] {symbol}")
            historical_downloader.download_symbol_data(
                symbol=symbol,
                interval=args.interval,
                days_back=args.days,
                save_to_db=True
            )

        print("\n" + "=" * 60)
        print("✅ Data download complete!")
        print("=" * 60)
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Download error: {e}")
        log.exception(e)
        return 1


if __name__ == "__main__":
    exit(main())

"""
System health check script.
Validates all components are working correctly.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from src.database import db, init_database
from src.data_collection import binance_client
from src.utils import log


def check_configuration():
    """Check configuration."""
    print("\n1️⃣  Configuration")
    print("-" * 60)

    print(f"Trading Mode: {settings.trading.trading_mode}")
    print(f"Target Symbols: {', '.join(settings.trading.target_symbols)}")
    print(f"Database: {settings.database.database_url}")

    missing = settings.validate_required_keys()
    if missing:
        print(f"\n⚠️  Missing configuration: {', '.join(missing)}")
        return False
    else:
        print("\n✅ Configuration OK")
        return True


def check_database():
    """Check database connection."""
    print("\n2️⃣  Database")
    print("-" * 60)

    try:
        init_database()
        if db.check_connection():
            print("✅ Database connection OK")

            # Show table counts
            tables = ['ohlcv', 'sentiment_data', 'features', 'predictions', 'trades']
            print("\nTable row counts:")
            for table in tables:
                try:
                    count = db.get_table_count(table)
                    print(f"  {table:20s}: {count:>6,} rows")
                except Exception as e:
                    print(f"  {table:20s}: ERROR - {e}")

            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_binance_api():
    """Check Binance API connection."""
    print("\n3️⃣  Binance API")
    print("-" * 60)

    try:
        # Test ping
        if not binance_client.ping():
            print("❌ Binance API ping failed")
            return False

        print("✅ API connection OK")

        # Get server time
        server_time = binance_client.get_server_time()
        print(f"Server time: {server_time}")

        # Test market data
        try:
            price = binance_client.get_price("BTC/USDT")
            print(f"BTC/USDT price: ${price:,.2f}")

            ticker = binance_client.get_ticker("BTC/USDT")
            print(f"24h change: {float(ticker['priceChangePercent']):+.2f}%")

            print("\n✅ Market data access OK")
        except Exception as e:
            print(f"⚠️  Market data error: {e}")

        # Test account access (if API keys provided)
        if settings.binance.api_key and settings.binance.api_secret:
            try:
                balances = binance_client.get_account_balance()
                print(f"\nAccount has {len(balances)} assets with balance")

                # Show USDT balance
                usdt_balance = balances.get('USDT', {}).get('total', 0)
                print(f"USDT balance: {usdt_balance:.2f}")

                print("\n✅ Account access OK")
            except Exception as e:
                print(f"⚠️  Account access error: {e}")

        return True

    except Exception as e:
        print(f"❌ Binance API error: {e}")
        return False


def check_dependencies():
    """Check Python dependencies."""
    print("\n4️⃣  Dependencies")
    print("-" * 60)

    critical_modules = [
        'pandas',
        'numpy',
        'ccxt',
        'binance',
        'sqlalchemy',
        'sklearn',
        'xgboost',
        'torch',
        'tensorflow',
        'streamlit',
    ]

    missing = []
    for module in critical_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - NOT INSTALLED")
            missing.append(module)

    if missing:
        print(f"\n⚠️  Missing modules: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed")
        return True


def main():
    """Run all health checks."""
    print("=" * 60)
    print("SYSTEM HEALTH CHECK")
    print("=" * 60)

    results = []

    # Run checks
    results.append(("Configuration", check_configuration()))
    results.append(("Database", check_database()))
    results.append(("Binance API", check_binance_api()))
    results.append(("Dependencies", check_dependencies()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20s}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All systems operational!")
        print("\nYou can now:")
        print("  1. Download data: python scripts/download_data.py")
        print("  2. Start bot (paper): python main.py --mode paper")
        print("  3. Start dashboard: streamlit run src/dashboard/app.py")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

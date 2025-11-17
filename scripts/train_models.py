"""
Train ML models for price prediction.
"""
import sys
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_database, db, OHLCVRepository
from src.feature_engineering import calculate_indicators_for_symbol
from src.models.classifier import PriceClassifier
from config import settings
from src.utils import log


def train_model_for_symbol(symbol: str, interval: str = '1h', horizon: int = 6):
    """
    Train model for a symbol.

    Args:
        symbol: Trading symbol
        interval: Timeframe
        horizon: Prediction horizon in periods
    """
    print(f"\n{'='*60}")
    print(f"Training model for {symbol} ({interval} timeframe)")
    print(f"{'='*60}")

    # Get data from database
    with db.session_scope() as session:
        ohlcv_data = OHLCVRepository.get_latest(session, symbol, interval, limit=2000)

        if len(ohlcv_data) < 500:
            print(f"❌ Insufficient data for {symbol} ({len(ohlcv_data)} candles)")
            print(f"   Download more data using: python scripts/download_data.py")
            return None

        # Convert to DataFrame
        df = OHLCVRepository.to_dataframe(ohlcv_data)

    print(f"Loaded {len(df)} candles from database")

    # Calculate indicators
    print("Calculating technical indicators...")
    df = calculate_indicators_for_symbol(df)

    print(f"After indicators: {df.shape}")

    # Train classifier
    classifier = PriceClassifier()
    metrics = classifier.train(df, test_size=0.2, horizon=horizon)

    print(f"\n✅ Training complete!")
    print(f"   Accuracy: {metrics['accuracy']:.2%}")

    # Show top features
    feature_importance = metrics['feature_importance']
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]

    print(f"\nTop 10 Features:")
    for feat, importance in top_features:
        print(f"   {feat:20s}: {importance:.4f}")

    # Save model
    model_path = project_root / "data" / "models" / f"{symbol.replace('/', '_')}_{interval}.pkl"
    classifier.save_model(str(model_path))

    print(f"\n💾 Model saved to: {model_path}")

    return classifier


def main():
    """Train models for all configured symbols."""
    parser = argparse.ArgumentParser(description='Train ML models for price prediction')
    parser.add_argument('--symbols', type=str, help='Comma-separated symbols (default from config)')
    parser.add_argument('--interval', type=str, default='1h', help='Timeframe (default: 1h)')
    parser.add_argument('--horizon', type=int, default=6, help='Prediction horizon in periods (default: 6)')

    args = parser.parse_args()

    print("=" * 60)
    print("MODEL TRAINING")
    print("=" * 60)

    # Initialize database
    print("\nInitializing database...")
    init_database()

    # Get symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        symbols = settings.trading.target_symbols

    print(f"\nTraining models for: {', '.join(symbols)}")
    print(f"Interval: {args.interval}")
    print(f"Horizon: {args.horizon} periods")

    # Train each symbol
    results = {}
    for symbol in symbols:
        try:
            classifier = train_model_for_symbol(symbol, args.interval, args.horizon)
            if classifier:
                results[symbol] = "✅ Success"
        except Exception as e:
            print(f"\n❌ Error training {symbol}: {e}")
            log.exception(e)
            results[symbol] = f"❌ Failed: {e}"

    # Summary
    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)

    for symbol, status in results.items():
        print(f"{symbol:15s}: {status}")

    print("\n✅ Training complete!")
    print("\nNext steps:")
    print("  1. Test predictions: python -c \"from src.models.classifier import PriceClassifier; ...\"")
    print("  2. Run backtest: python scripts/backtest.py")
    print("  3. Start bot: python main_enhanced.py --mode paper")


if __name__ == "__main__":
    main()

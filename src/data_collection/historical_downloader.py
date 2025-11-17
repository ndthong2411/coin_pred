"""
Historical data downloader for backtesting and model training.
"""
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from tqdm import tqdm
from config import settings
from src.utils import log
from src.database import db, OHLCVRepository
from .binance_client import binance_client


class HistoricalDataDownloader:
    """Download and store historical market data."""

    def __init__(self):
        self.client = binance_client

    def download_symbol_data(
        self,
        symbol: str,
        interval: str = '1m',
        days_back: int = 30,
        save_to_db: bool = True
    ) -> pd.DataFrame:
        """
        Download historical data for a symbol.

        Args:
            symbol: Trading symbol
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            days_back: Number of days to download
            save_to_db: Save to database

        Returns:
            DataFrame with OHLCV data
        """
        log.info(f"Downloading {days_back} days of {interval} data for {symbol}")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)

        all_data = []
        current_start = start_time

        # Binance limit is 1000 candles per request
        max_candles = 1000

        with tqdm(total=days_back, desc=f"Downloading {symbol}") as pbar:
            while current_start < end_time:
                try:
                    df = self.client.get_historical_klines(
                        symbol=symbol,
                        interval=interval,
                        start_time=current_start,
                        end_time=end_time,
                        limit=max_candles
                    )

                    if df.empty:
                        break

                    all_data.append(df)

                    # Move to next batch
                    current_start = df.index[-1] + timedelta(minutes=1)
                    pbar.update((datetime.utcnow() - current_start).days / days_back)

                except Exception as e:
                    log.error(f"Error downloading data: {e}")
                    break

        if not all_data:
            log.warning(f"No data downloaded for {symbol}")
            return pd.DataFrame()

        # Combine all dataframes
        final_df = pd.concat(all_data)
        final_df = final_df[~final_df.index.duplicated(keep='last')]
        final_df.sort_index(inplace=True)

        log.info(f"Downloaded {len(final_df)} candles for {symbol}")

        # Save to database
        if save_to_db:
            self._save_to_database(symbol, interval, final_df)

        return final_df

    def _save_to_database(self, symbol: str, timeframe: str, df: pd.DataFrame):
        """Save DataFrame to database."""
        log.info(f"Saving {len(df)} records to database")

        records = []
        for timestamp, row in df.iterrows():
            records.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': timestamp,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            })

        # Bulk insert
        try:
            with db.session_scope() as session:
                OHLCVRepository.bulk_insert(session, records)
            log.info(f"Saved {len(records)} records for {symbol}")
        except Exception as e:
            log.error(f"Error saving to database: {e}")

    def download_all_symbols(
        self,
        symbols: List[str] = None,
        interval: str = '1m',
        days_back: int = 30
    ):
        """
        Download data for all configured symbols.

        Args:
            symbols: List of symbols (default from settings)
            interval: Timeframe
            days_back: Days to download
        """
        symbols = symbols or settings.trading.target_symbols

        log.info(f"Downloading data for {len(symbols)} symbols")

        for symbol in symbols:
            try:
                self.download_symbol_data(symbol, interval, days_back)
            except Exception as e:
                log.error(f"Failed to download {symbol}: {e}")


# Global downloader instance
historical_downloader = HistoricalDataDownloader()


if __name__ == "__main__":
    from src.database import init_database

    # Initialize database
    init_database()

    # Download sample data
    print("Downloading historical data...")

    downloader = HistoricalDataDownloader()
    df = downloader.download_symbol_data("BTC/USDT", interval="1h", days_back=7)

    print(f"\n✅ Downloaded {len(df)} candles")
    print("\nSample data:")
    print(df.head())
    print(df.tail())

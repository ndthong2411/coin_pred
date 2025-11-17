"""
Technical indicators calculator.
Implements 50+ indicators for trading signals.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
import pandas_ta as ta
from src.utils import log


class TechnicalIndicators:
    """Calculate technical indicators from OHLCV data."""

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame.

        Args:
            df: DataFrame with OHLCV columns

        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()

        # Momentum indicators
        df = TechnicalIndicators.add_momentum_indicators(df)

        # Trend indicators
        df = TechnicalIndicators.add_trend_indicators(df)

        # Volatility indicators
        df = TechnicalIndicators.add_volatility_indicators(df)

        # Volume indicators
        df = TechnicalIndicators.add_volume_indicators(df)

        # Price action
        df = TechnicalIndicators.add_price_action(df)

        return df

    @staticmethod
    def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators."""
        # RSI (Relative Strength Index)
        df['rsi_14'] = ta.rsi(df['close'], length=14)
        df['rsi_9'] = ta.rsi(df['close'], length=9)
        df['rsi_21'] = ta.rsi(df['close'], length=21)

        # Stochastic Oscillator
        stoch = ta.stoch(df['high'], df['low'], df['close'])
        if stoch is not None:
            df['stoch_k'] = stoch['STOCHk_14_3_3']
            df['stoch_d'] = stoch['STOCHd_14_3_3']

        # Williams %R
        df['williams_r'] = ta.willr(df['high'], df['low'], df['close'])

        # Rate of Change
        df['roc'] = ta.roc(df['close'], length=10)

        # Commodity Channel Index
        df['cci'] = ta.cci(df['high'], df['low'], df['close'])

        return df

    @staticmethod
    def add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators."""
        # Moving Averages
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_21'] = ta.ema(df['close'], length=21)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['ema_200'] = ta.ema(df['close'], length=200)

        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)

        # MACD
        macd = ta.macd(df['close'])
        if macd is not None:
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']

        # ADX (Average Directional Index)
        adx = ta.adx(df['high'], df['low'], df['close'])
        if adx is not None:
            df['adx'] = adx['ADX_14']
            df['adx_plus'] = adx['DMP_14']
            df['adx_minus'] = adx['DMN_14']

        # Parabolic SAR
        psar = ta.psar(df['high'], df['low'], df['close'])
        if psar is not None:
            df['psar'] = psar['PSARl_0.02_0.2']

        # Supertrend
        supertrend = ta.supertrend(df['high'], df['low'], df['close'])
        if supertrend is not None:
            df['supertrend'] = supertrend['SUPERT_7_3.0']

        return df

    @staticmethod
    def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators."""
        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20)
        if bb is not None:
            df['bb_upper'] = bb['BBU_20_2.0']
            df['bb_middle'] = bb['BBM_20_2.0']
            df['bb_lower'] = bb['BBL_20_2.0']
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # ATR (Average True Range)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_percent'] = (df['atr'] / df['close']) * 100

        # Keltner Channels
        kc = ta.kc(df['high'], df['low'], df['close'])
        if kc is not None:
            df['kc_upper'] = kc['KCUe_20_2']
            df['kc_middle'] = kc['KCBe_20_2']
            df['kc_lower'] = kc['KCLe_20_2']

        # Donchian Channels
        dc = ta.donchian(df['high'], df['low'])
        if dc is not None:
            df['dc_upper'] = dc['DCU_20_20']
            df['dc_middle'] = dc['DCM_20_20']
            df['dc_lower'] = dc['DCL_20_20']

        return df

    @staticmethod
    def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators."""
        # On-Balance Volume
        df['obv'] = ta.obv(df['close'], df['volume'])

        # Volume Weighted Average Price
        df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

        # Money Flow Index
        df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'])

        # Accumulation/Distribution Index
        df['ad'] = ta.ad(df['high'], df['low'], df['close'], df['volume'])

        # Chaikin Money Flow
        df['cmf'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'])

        # Volume Rate of Change
        df['volume_roc'] = ta.roc(df['volume'], length=10)

        return df

    @staticmethod
    def add_price_action(df: pd.DataFrame) -> pd.DataFrame:
        """Add price action features."""
        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = df['close'].diff()

        # High-Low range
        df['hl_range'] = df['high'] - df['low']
        df['hl_range_pct'] = (df['hl_range'] / df['close']) * 100

        # Open-Close range
        df['oc_range'] = abs(df['open'] - df['close'])
        df['oc_range_pct'] = (df['oc_range'] / df['close']) * 100

        # Upper/Lower shadows
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']

        # Body size
        df['body_size'] = abs(df['close'] - df['open'])
        df['body_pct'] = (df['body_size'] / df['hl_range']).replace([np.inf, -np.inf], 0)

        # Candle type
        df['is_green'] = (df['close'] > df['open']).astype(int)
        df['is_red'] = (df['close'] < df['open']).astype(int)
        df['is_doji'] = (df['body_pct'] < 0.1).astype(int)

        # Support/Resistance levels (simplified)
        df['swing_high'] = df['high'].rolling(window=5, center=True).max()
        df['swing_low'] = df['low'].rolling(window=5, center=True).min()

        return df

    @staticmethod
    def calculate_pivot_points(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate pivot points."""
        # Standard Pivot Points
        df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
        df['r1'] = 2 * df['pivot'] - df['low']
        df['r2'] = df['pivot'] + (df['high'] - df['low'])
        df['r3'] = df['high'] + 2 * (df['pivot'] - df['low'])
        df['s1'] = 2 * df['pivot'] - df['high']
        df['s2'] = df['pivot'] - (df['high'] - df['low'])
        df['s3'] = df['low'] - 2 * (df['high'] - df['pivot'])

        return df

    @staticmethod
    def add_custom_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add custom engineered features."""
        # Trend strength
        df['trend_strength'] = abs(df['ema_9'] - df['ema_21']) / df['close']

        # Momentum score
        df['momentum_score'] = (
            ((df['rsi_14'] - 50) / 50) +
            ((df['macd_hist'] / df['close']).fillna(0)) +
            ((df['roc'] / 100).fillna(0))
        ) / 3

        # Volatility score
        df['volatility_score'] = (
            df['atr_percent'] + df['bb_width']
        ) / 2

        # Volume strength
        df['volume_strength'] = df['volume'] / df['volume'].rolling(20).mean()

        # Price position in BB
        df['price_bb_position'] = (
            (df['close'] - df['bb_lower']) /
            (df['bb_upper'] - df['bb_lower'])
        ).replace([np.inf, -np.inf], np.nan)

        return df

    @staticmethod
    def get_signal_strength(df: pd.DataFrame) -> pd.Series:
        """
        Calculate overall signal strength (-1 to +1).

        Returns:
            Series with signal strength values
        """
        signals = []

        # RSI signal
        rsi = df['rsi_14']
        rsi_signal = np.where(rsi < 30, 1,
                              np.where(rsi > 70, -1, 0))
        signals.append(rsi_signal)

        # MACD signal
        macd_signal = np.where(df['macd'] > df['macd_signal'], 1,
                               np.where(df['macd'] < df['macd_signal'], -1, 0))
        signals.append(macd_signal)

        # EMA crossover
        ema_signal = np.where(df['ema_9'] > df['ema_21'], 1,
                              np.where(df['ema_9'] < df['ema_21'], -1, 0))
        signals.append(ema_signal)

        # Combine signals
        combined = np.mean(signals, axis=0)
        return pd.Series(combined, index=df.index)


def calculate_indicators_for_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main function to calculate all indicators for a symbol.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with all indicators
    """
    if df.empty:
        return df

    try:
        indicators = TechnicalIndicators()
        df = indicators.add_all_indicators(df)
        df = indicators.add_custom_features(df)
        df = indicators.calculate_pivot_points(df)

        # Drop NaN rows (from indicator calculations)
        df = df.dropna()

        log.debug(f"Calculated {len(df.columns)} features")
        return df

    except Exception as e:
        log.error(f"Error calculating indicators: {e}")
        return df


if __name__ == "__main__":
    # Test indicators
    from src.data_collection.binance_client import binance_client

    print("Testing technical indicators...")

    # Get sample data
    df = binance_client.get_historical_klines("BTC/USDT", "1h", limit=200)

    print(f"Initial shape: {df.shape}")

    # Calculate indicators
    df_with_indicators = calculate_indicators_for_symbol(df)

    print(f"After indicators: {df_with_indicators.shape}")
    print(f"\nColumns: {list(df_with_indicators.columns)[:20]}...")
    print(f"\nSample data:")
    print(df_with_indicators[['close', 'rsi_14', 'macd', 'ema_9', 'bb_upper']].tail())

    print("\n✅ Indicators test complete")

"""
Unit tests for technical indicators.
"""
import pytest
import pandas as pd
import numpy as np

from src.feature_engineering.indicators import TechnicalIndicators


@pytest.mark.unit
class TestTechnicalIndicators:
    """Test technical indicators calculations."""

    def test_add_momentum_indicators(self, sample_ohlcv_data):
        """Test adding momentum indicators."""
        df = TechnicalIndicators.add_momentum_indicators(sample_ohlcv_data)

        # Check RSI
        assert 'rsi_14' in df.columns
        assert 'rsi_9' in df.columns
        assert df['rsi_14'].notna().any()

        # RSI should be between 0 and 100
        rsi_values = df['rsi_14'].dropna()
        assert (rsi_values >= 0).all()
        assert (rsi_values <= 100).all()

    def test_add_trend_indicators(self, sample_ohlcv_data):
        """Test adding trend indicators."""
        df = TechnicalIndicators.add_trend_indicators(sample_ohlcv_data)

        # Check EMAs
        assert 'ema_9' in df.columns
        assert 'ema_21' in df.columns
        assert 'ema_50' in df.columns
        assert df['ema_9'].notna().any()

        # Check MACD
        assert 'macd' in df.columns
        assert 'macd_signal' in df.columns

    def test_add_volatility_indicators(self, sample_ohlcv_data):
        """Test adding volatility indicators."""
        df = TechnicalIndicators.add_volatility_indicators(sample_ohlcv_data)

        # Check Bollinger Bands
        assert 'bb_upper' in df.columns
        assert 'bb_middle' in df.columns
        assert 'bb_lower' in df.columns

        # Upper should be > middle > lower
        valid_rows = df[['bb_upper', 'bb_middle', 'bb_lower']].dropna()
        if len(valid_rows) > 0:
            assert (valid_rows['bb_upper'] >= valid_rows['bb_middle']).all()
            assert (valid_rows['bb_middle'] >= valid_rows['bb_lower']).all()

    def test_add_volume_indicators(self, sample_ohlcv_data):
        """Test adding volume indicators."""
        df = TechnicalIndicators.add_volume_indicators(sample_ohlcv_data)

        # Check OBV
        assert 'obv' in df.columns

        # Check VWAP
        assert 'vwap' in df.columns

    def test_add_price_action(self, sample_ohlcv_data):
        """Test adding price action indicators."""
        df = TechnicalIndicators.add_price_action(sample_ohlcv_data)

        # Check returns
        assert 'returns' in df.columns

        # Returns should be reasonable
        returns = df['returns'].dropna()
        assert returns.abs().max() < 1.0  # No more than 100% change

    def test_add_all_indicators(self, sample_ohlcv_data):
        """Test adding all indicators at once."""
        df = TechnicalIndicators.add_all_indicators(sample_ohlcv_data)

        # Should have many indicator columns
        assert len(df.columns) > len(sample_ohlcv_data.columns)

        # Check some key indicators exist
        assert 'rsi_14' in df.columns
        assert 'ema_21' in df.columns
        assert 'bb_upper' in df.columns
        assert 'macd' in df.columns

    def test_indicators_with_insufficient_data(self):
        """Test indicators with very small dataset."""
        # Create tiny dataset
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200]
        })

        # Should not crash, but many indicators will be NaN
        result = TechnicalIndicators.add_all_indicators(df)

        assert len(result) == len(df)
        assert 'rsi_14' in result.columns

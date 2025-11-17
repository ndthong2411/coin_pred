"""
Unit tests for SignalGenerator.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.trading.signal_generator import SignalGenerator


@pytest.mark.unit
class TestSignalGenerator:
    """Test SignalGenerator class."""

    def test_initialization(self):
        """Test signal generator initialization."""
        sg = SignalGenerator()
        assert sg.min_confidence > 0

    def test_generate_signal_insufficient_data(self):
        """Test signal generation with insufficient data."""
        sg = SignalGenerator()

        # Empty DataFrame
        df = pd.DataFrame()
        signal = sg.generate_signal(df)

        assert signal['action'] == 'HOLD'
        assert signal['confidence'] == 0.0
        assert 'Insufficient data' in signal['reasons'][0]

    def test_generate_signal_small_dataset(self):
        """Test signal with less than minimum required data."""
        sg = SignalGenerator()

        # Only 10 rows
        df = pd.DataFrame({
            'close': [45000 + i*100 for i in range(10)],
            'rsi_14': [50] * 10,
            'macd': [0] * 10,
            'macd_signal': [0] * 10
        })

        signal = sg.generate_signal(df)
        assert signal['action'] == 'HOLD'

    def test_technical_signal_rsi_oversold(self):
        """Test technical signal with oversold RSI."""
        sg = SignalGenerator()

        df = self._create_sample_df(
            n=100,
            rsi=25,  # Oversold
            macd=10,
            macd_signal=5,
            close=45000
        )

        signal = sg._technical_signal(df)

        assert signal['action'] == 'BUY'
        assert signal['confidence'] > 0
        assert any('RSI oversold' in r for r in signal['reasons'])

    def test_technical_signal_rsi_overbought(self):
        """Test technical signal with overbought RSI."""
        sg = SignalGenerator()

        df = self._create_sample_df(
            n=100,
            rsi=75,  # Overbought
            macd=-10,
            macd_signal=-5,
            close=45000
        )

        signal = sg._technical_signal(df)

        assert signal['action'] == 'SELL'
        assert signal['confidence'] > 0
        assert any('RSI overbought' in r for r in signal['reasons'])

    def test_technical_signal_macd_bullish(self):
        """Test technical signal with bullish MACD."""
        sg = SignalGenerator()

        df = self._create_sample_df(
            n=100,
            rsi=50,
            macd=100,
            macd_signal=50,  # MACD above signal
            close=45000
        )

        signal = sg._technical_signal(df)

        assert 'BUY' in signal['action'] or 'HOLD' in signal['action']
        assert any('MACD bullish' in r for r in signal['reasons'])

    def test_trend_signal_strong_uptrend(self):
        """Test trend signal with strong uptrend."""
        sg = SignalGenerator()

        df = self._create_sample_df(
            n=100,
            ema_9=45500,
            ema_21=45000,
            ema_50=44500,
            adx=30  # Strong trend
        )

        signal = sg._trend_signal(df)

        assert signal['action'] == 'BUY'
        assert signal['confidence'] > 0
        assert any('uptrend' in r.lower() for r in signal['reasons'])

    def test_trend_signal_strong_downtrend(self):
        """Test trend signal with strong downtrend."""
        sg = SignalGenerator()

        df = self._create_sample_df(
            n=100,
            ema_9=44500,
            ema_21=45000,
            ema_50=45500,
            adx=30
        )

        signal = sg._trend_signal(df)

        assert signal['action'] == 'SELL'
        assert signal['confidence'] > 0
        assert any('downtrend' in r.lower() for r in signal['reasons'])

    def test_mean_reversion_signal_oversold(self):
        """Test mean reversion signal near lower BB."""
        sg = SignalGenerator()

        df = self._create_sample_df(
            n=100,
            bb_pct=0.15,  # Near lower band
            rsi=22,  # Extreme oversold
            close=45000
        )

        signal = sg._mean_reversion_signal(df)

        assert signal['action'] == 'BUY'
        assert signal['confidence'] > 0

    def test_mean_reversion_signal_overbought(self):
        """Test mean reversion signal near upper BB."""
        sg = SignalGenerator()

        df = self._create_sample_df(
            n=100,
            bb_pct=0.85,  # Near upper band
            rsi=78,  # Extreme overbought
            close=45000
        )

        signal = sg._mean_reversion_signal(df)

        assert signal['action'] == 'SELL'
        assert signal['confidence'] > 0

    def test_momentum_signal_upward(self):
        """Test momentum signal with upward price movement."""
        sg = SignalGenerator()

        # Create upward trending prices
        prices = [44000 + i*50 for i in range(100)]
        df = pd.DataFrame({
            'close': prices,
            'volume_strength': [1.8] * 100
        })

        signal = sg._momentum_signal(df)

        # Should be BUY or HOLD (upward momentum)
        assert signal['action'] in ['BUY', 'HOLD']

    def test_momentum_signal_downward(self):
        """Test momentum signal with downward price movement."""
        sg = SignalGenerator()

        # Create downward trending prices
        prices = [45000 - i*50 for i in range(100)]
        df = pd.DataFrame({
            'close': prices,
            'volume_strength': [1.0] * 100
        })

        signal = sg._momentum_signal(df)

        # Should be SELL or HOLD (downward momentum)
        assert signal['action'] in ['SELL', 'HOLD']

    def test_model_signal(self):
        """Test model signal generation."""
        sg = SignalGenerator()

        predictions = {
            'prediction': 'UP',
            'confidence': 0.85,
            'model': 'XGBoost'
        }

        signal = sg._model_signal(predictions)

        assert signal['action'] == 'UP'
        assert signal['confidence'] == 0.85
        assert signal['weight'] == 0.4

    def test_combine_signals_all_buy(self):
        """Test combining signals when all suggest BUY."""
        sg = SignalGenerator()

        signals = [
            {'action': 'BUY', 'confidence': 0.8, 'reasons': ['Reason 1'], 'weight': 0.5},
            {'action': 'BUY', 'confidence': 0.7, 'reasons': ['Reason 2'], 'weight': 0.5},
        ]

        latest_candle = pd.Series({'close': 45000})

        signal = sg._combine_signals(signals, latest_candle)

        assert signal['action'] == 'BUY'
        assert signal['confidence'] > 0
        assert signal['current_price'] == 45000

    def test_combine_signals_mixed(self):
        """Test combining mixed signals."""
        sg = SignalGenerator()

        signals = [
            {'action': 'BUY', 'confidence': 0.6, 'reasons': ['Buy reason'], 'weight': 0.3},
            {'action': 'SELL', 'confidence': 0.5, 'reasons': ['Sell reason'], 'weight': 0.3},
            {'action': 'BUY', 'confidence': 0.8, 'reasons': ['Strong buy'], 'weight': 0.4},
        ]

        latest_candle = pd.Series({'close': 45000})

        signal = sg._combine_signals(signals, latest_candle)

        # Should favor BUY due to higher weighted score
        assert signal['action'] == 'BUY'

    def test_combine_signals_low_confidence(self):
        """Test combining signals with confidence below minimum."""
        sg = SignalGenerator()
        sg.min_confidence = 0.7  # High threshold

        signals = [
            {'action': 'BUY', 'confidence': 0.3, 'reasons': ['Weak buy'], 'weight': 0.5},
            {'action': 'SELL', 'confidence': 0.2, 'reasons': ['Weak sell'], 'weight': 0.5},
        ]

        latest_candle = pd.Series({'close': 45000})

        signal = sg._combine_signals(signals, latest_candle)

        # Should return HOLD due to low confidence
        assert signal['action'] == 'HOLD'

    def test_generate_signal_with_predictions(self, sample_ohlcv_data):
        """Test full signal generation with model predictions."""
        sg = SignalGenerator()
        sg.min_confidence = 0.3  # Lower for testing

        # Add indicators to sample data
        df = sample_ohlcv_data.copy()
        df['rsi_14'] = 65
        df['macd'] = 10
        df['macd_signal'] = 5
        df['ema_9'] = 45500
        df['ema_21'] = 45000
        df['ema_50'] = 44500
        df['bb_upper'] = 46000
        df['bb_lower'] = 44000
        df['bb_pct'] = 0.5
        df['adx'] = 25
        df['volume_strength'] = 1.2

        predictions = {
            'prediction': 'UP',
            'confidence': 0.85,
            'model': 'XGBoost'
        }

        signal = sg.generate_signal(df, predictions)

        assert signal['action'] in ['BUY', 'SELL', 'HOLD']
        assert 'confidence' in signal
        assert 'reasons' in signal
        assert 'current_price' in signal
        assert 'signals_breakdown' in signal

    def test_generate_signal_without_predictions(self, sample_ohlcv_data):
        """Test signal generation without model predictions."""
        sg = SignalGenerator()
        sg.min_confidence = 0.3

        df = sample_ohlcv_data.copy()
        df['rsi_14'] = 50
        df['macd'] = 0
        df['macd_signal'] = 0
        df['ema_9'] = 45000
        df['ema_21'] = 45000
        df['ema_50'] = 45000
        df['bb_upper'] = 46000
        df['bb_lower'] = 44000
        df['bb_pct'] = 0.5
        df['adx'] = 20
        df['volume_strength'] = 1.0

        signal = sg.generate_signal(df, predictions=None)

        assert signal['action'] in ['BUY', 'SELL', 'HOLD']
        assert 'confidence' in signal
        assert 'reasons' in signal

    def test_no_signal(self):
        """Test no signal generation."""
        sg = SignalGenerator()

        signal = sg._no_signal("Test reason")

        assert signal['action'] == 'HOLD'
        assert signal['confidence'] == 0.0
        assert signal['reasons'] == ["Test reason"]

    # Helper methods
    def _create_sample_df(self, n=100, **kwargs):
        """Create sample DataFrame with specified indicators."""
        data = {
            'close': [45000] * n,
            'rsi_14': [50] * n,
            'macd': [0] * n,
            'macd_signal': [0] * n,
            'ema_9': [45000] * n,
            'ema_21': [45000] * n,
            'ema_50': [45000] * n,
            'bb_upper': [46000] * n,
            'bb_lower': [44000] * n,
            'bb_pct': [0.5] * n,
            'adx': [20] * n,
            'volume_strength': [1.0] * n
        }

        # Override with kwargs
        for key, value in kwargs.items():
            data[key] = [value] * n

        return pd.DataFrame(data)

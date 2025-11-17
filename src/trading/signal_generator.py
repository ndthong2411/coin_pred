"""
Trading signal generator from technical indicators and predictions.
"""
from typing import Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from config import settings
from src.utils import log
from src.feature_engineering import calculate_indicators_for_symbol


class SignalGenerator:
    """Generate trading signals from indicators and predictions."""

    def __init__(self):
        """Initialize signal generator."""
        self.min_confidence = settings.trading.min_confidence_score
        log.info(f"Signal Generator initialized (min confidence: {self.min_confidence:.0%})")

    def generate_signal(
        self,
        df: pd.DataFrame,
        predictions: Optional[Dict] = None
    ) -> Dict:
        """
        Generate trading signal from data.

        Args:
            df: DataFrame with OHLCV and indicators
            predictions: Optional model predictions

        Returns:
            Signal dict with action, confidence, and reason
        """
        if df.empty or len(df) < 50:
            return self._no_signal("Insufficient data")

        # Get latest candle
        latest = df.iloc[-1]

        # Calculate signals from different strategies
        signals = []

        # 1. Technical indicator signals
        tech_signal = self._technical_signal(df)
        signals.append(tech_signal)

        # 2. Trend following signal
        trend_signal = self._trend_signal(df)
        signals.append(trend_signal)

        # 3. Mean reversion signal
        reversion_signal = self._mean_reversion_signal(df)
        signals.append(reversion_signal)

        # 4. Momentum signal
        momentum_signal = self._momentum_signal(df)
        signals.append(momentum_signal)

        # 5. Model prediction signal (if available)
        if predictions:
            model_signal = self._model_signal(predictions)
            signals.append(model_signal)

        # Combine signals
        combined_signal = self._combine_signals(signals, latest)

        return combined_signal

    def _technical_signal(self, df: pd.DataFrame) -> Dict:
        """Generate signal from technical indicators."""
        latest = df.iloc[-1]
        score = 0
        reasons = []

        # RSI
        rsi = latest.get('rsi_14', 50)
        if rsi < 30:
            score += 1
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 1
            reasons.append("RSI overbought")

        # MACD
        macd = latest.get('macd', 0)
        macd_signal = latest.get('macd_signal', 0)
        if macd > macd_signal:
            score += 1
            reasons.append("MACD bullish")
        elif macd < macd_signal:
            score -= 1
            reasons.append("MACD bearish")

        # Bollinger Bands
        close = latest['close']
        bb_lower = latest.get('bb_lower', close)
        bb_upper = latest.get('bb_upper', close)

        if close < bb_lower:
            score += 1
            reasons.append("Price below BB lower")
        elif close > bb_upper:
            score -= 1
            reasons.append("Price above BB upper")

        # Normalize score
        action = "BUY" if score > 0 else "SELL" if score < 0 else "HOLD"
        confidence = min(abs(score) / 3.0, 1.0)

        return {
            'action': action,
            'confidence': confidence,
            'reasons': reasons,
            'weight': 0.3
        }

    def _trend_signal(self, df: pd.DataFrame) -> Dict:
        """Generate signal from trend following."""
        latest = df.iloc[-1]
        score = 0
        reasons = []

        # EMA crossover
        ema_9 = latest.get('ema_9', 0)
        ema_21 = latest.get('ema_21', 0)
        ema_50 = latest.get('ema_50', 0)

        if ema_9 > ema_21 > ema_50:
            score += 2
            reasons.append("Strong uptrend (EMA)")
        elif ema_9 < ema_21 < ema_50:
            score -= 2
            reasons.append("Strong downtrend (EMA)")

        # ADX (trend strength)
        adx = latest.get('adx', 0)
        if adx > 25:
            if ema_9 > ema_21:
                score += 1
                reasons.append("Strong trend confirmed")

        action = "BUY" if score > 0 else "SELL" if score < 0 else "HOLD"
        confidence = min(abs(score) / 3.0, 1.0)

        return {
            'action': action,
            'confidence': confidence,
            'reasons': reasons,
            'weight': 0.25
        }

    def _mean_reversion_signal(self, df: pd.DataFrame) -> Dict:
        """Generate signal from mean reversion."""
        latest = df.iloc[-1]
        score = 0
        reasons = []

        # Bollinger Band position
        bb_pct = latest.get('bb_pct', 0.5)

        if bb_pct < 0.2:
            score += 1
            reasons.append("Near BB lower (reversion)")
        elif bb_pct > 0.8:
            score -= 1
            reasons.append("Near BB upper (reversion)")

        # RSI mean reversion
        rsi = latest.get('rsi_14', 50)
        if rsi < 25:
            score += 1
            reasons.append("Extreme oversold")
        elif rsi > 75:
            score -= 1
            reasons.append("Extreme overbought")

        action = "BUY" if score > 0 else "SELL" if score < 0 else "HOLD"
        confidence = min(abs(score) / 2.0, 1.0)

        return {
            'action': action,
            'confidence': confidence,
            'reasons': reasons,
            'weight': 0.2
        }

    def _momentum_signal(self, df: pd.DataFrame) -> Dict:
        """Generate signal from momentum indicators."""
        latest = df.iloc[-1]
        score = 0
        reasons = []

        # Price momentum
        if len(df) >= 10:
            price_change_5 = (df.iloc[-1]['close'] - df.iloc[-5]['close']) / df.iloc[-5]['close']

            if price_change_5 > 0.02:
                score += 1
                reasons.append("Strong upward momentum")
            elif price_change_5 < -0.02:
                score -= 1
                reasons.append("Strong downward momentum")

        # Volume
        volume_strength = latest.get('volume_strength', 1.0)
        if volume_strength > 1.5:
            # High volume confirms the move
            if score > 0:
                score += 0.5
                reasons.append("High volume confirmation")

        action = "BUY" if score > 0 else "SELL" if score < 0 else "HOLD"
        confidence = min(abs(score) / 2.0, 1.0)

        return {
            'action': action,
            'confidence': confidence,
            'reasons': reasons,
            'weight': 0.15
        }

    def _model_signal(self, predictions: Dict) -> Dict:
        """Generate signal from ML model predictions."""
        action = predictions.get('prediction', 'HOLD')
        confidence = predictions.get('confidence', 0.5)

        return {
            'action': action,
            'confidence': confidence,
            'reasons': [f"Model prediction ({predictions.get('model', 'unknown')})"],
            'weight': 0.4  # Higher weight for model predictions
        }

    def _combine_signals(self, signals: list, latest_candle: pd.Series) -> Dict:
        """Combine multiple signals into final decision."""
        if not signals:
            return self._no_signal("No signals available")

        # Weighted voting
        buy_score = 0
        sell_score = 0
        hold_score = 0
        all_reasons = []

        for signal in signals:
            action = signal['action']
            confidence = signal['confidence']
            weight = signal.get('weight', 1.0)
            weighted_confidence = confidence * weight

            if action == "BUY":
                buy_score += weighted_confidence
            elif action == "SELL":
                sell_score += weighted_confidence
            else:
                hold_score += weighted_confidence

            all_reasons.extend(signal['reasons'])

        # Determine final action
        max_score = max(buy_score, sell_score, hold_score)

        if max_score == buy_score and buy_score > 0:
            final_action = "BUY"
            final_confidence = buy_score / sum([s.get('weight', 1.0) for s in signals])
        elif max_score == sell_score and sell_score > 0:
            final_action = "SELL"
            final_confidence = sell_score / sum([s.get('weight', 1.0) for s in signals])
        else:
            final_action = "HOLD"
            final_confidence = 0.0

        # Check minimum confidence
        if final_confidence < self.min_confidence:
            return self._no_signal(f"Confidence too low ({final_confidence:.1%})")

        return {
            'action': final_action,
            'confidence': final_confidence,
            'reasons': all_reasons[:5],  # Top 5 reasons
            'current_price': latest_candle['close'],
            'timestamp': datetime.utcnow(),
            'signals_breakdown': {
                'buy_score': buy_score,
                'sell_score': sell_score,
                'hold_score': hold_score
            }
        }

    def _no_signal(self, reason: str) -> Dict:
        """Return no signal."""
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'reasons': [reason],
            'current_price': 0.0,
            'timestamp': datetime.utcnow()
        }


# Global signal generator
signal_generator = SignalGenerator()


if __name__ == "__main__":
    # Test signal generator
    from src.data_collection import binance_client

    print("Testing Signal Generator...")

    # Get data
    df = binance_client.get_historical_klines("BTC/USDT", "1h", limit=200)

    # Calculate indicators
    df = calculate_indicators_for_symbol(df)

    # Generate signal
    sg = SignalGenerator()
    signal = sg.generate_signal(df)

    print(f"\nSignal: {signal['action']}")
    print(f"Confidence: {signal['confidence']:.1%}")
    print(f"Price: ${signal['current_price']:,.2f}")
    print(f"Reasons:")
    for reason in signal['reasons']:
        print(f"  - {reason}")

    print("\n✅ Signal Generator test complete")

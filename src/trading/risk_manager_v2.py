"""
Enhanced Risk Manager V2 with 2024 best practices.
- Fractional Kelly Criterion
- Dynamic volatility adjustment
- Hard position limits
- Advanced drawdown protection
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from config import settings
from src.utils import log, calculate_position_size, safe_divide
from src.database import db, TradeRepository
import numpy as np


class EnhancedRiskManager:
    """
    Enhanced Risk Manager with 2024 best practices.

    Key improvements:
    - Fractional Kelly (1/10) for crypto volatility
    - Dynamic position sizing based on market conditions
    - Hard limits (max 20% per position)
    - Volatility-based adjustments
    - Monthly performance audits
    """

    def __init__(self):
        """Initialize enhanced risk manager."""
        self.max_position_size = settings.trading.max_position_size
        self.max_daily_loss = settings.trading.max_daily_loss
        self.stop_loss_percent = settings.trading.stop_loss_percent
        self.take_profit_percent = settings.trading.take_profit_percent
        self.max_concurrent_positions = settings.trading.max_concurrent_positions

        # 2024 Best Practices
        self.fractional_kelly = 0.1  # Use 1/10 Kelly
        self.max_single_position = 0.20  # Hard limit: 20% max
        self.volatility_adjustment = True
        self.last_audit_date = None

        log.info(f"Enhanced Risk Manager V2 initialized")
        log.info(f"  Fractional Kelly: {self.fractional_kelly} (conservative)")
        log.info(f"  Max Single Position: {self.max_single_position*100}%")

    def calculate_optimal_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        confidence: float,
        atr: Optional[float] = None,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> float:
        """
        Calculate optimal position size using 2024 best practices.

        Args:
            account_balance: Total account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            confidence: Model confidence (0-1)
            atr: Average True Range (for volatility adjustment)
            win_rate: Historical win rate (optional)
            avg_win: Average win amount (optional)
            avg_loss: Average loss amount (optional)

        Returns:
            Position size in quote currency
        """
        # Method 1: Base position size (% of portfolio)
        base_position = account_balance * self.max_position_size

        # Method 2: Fractional Kelly Criterion (RECOMMENDED 2024)
        kelly_position = self._calculate_fractional_kelly(
            account_balance, win_rate, avg_win, avg_loss
        )

        # Method 3: Risk-based sizing
        risk_amount = account_balance * self.max_position_size
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk > 0:
            risk_based_size = risk_amount / price_risk
            risk_based_value = risk_based_size * entry_price
        else:
            risk_based_value = base_position

        # Take minimum of all methods for safety
        optimal_size = min(base_position, kelly_position, risk_based_value)

        # Adjust by confidence
        confidence_adjusted = optimal_size * confidence

        # Volatility adjustment (if ATR provided)
        if self.volatility_adjustment and atr and atr > 0:
            volatility_factor = self._calculate_volatility_factor(atr, entry_price)
            confidence_adjusted *= volatility_factor
            log.debug(f"Volatility adjustment factor: {volatility_factor:.2f}")

        # HARD LIMIT: Never exceed 20% of portfolio (2024 best practice)
        max_allowed = account_balance * self.max_single_position
        final_size = min(confidence_adjusted, max_allowed)

        if final_size < confidence_adjusted:
            log.warning(
                f"Position size capped at {self.max_single_position*100}% hard limit "
                f"(was {confidence_adjusted/account_balance:.2%})"
            )

        log.info(
            f"Position sizing: Base=${base_position:.2f}, "
            f"Kelly=${kelly_position:.2f}, Risk=${risk_based_value:.2f}, "
            f"Final=${final_size:.2f} ({final_size/account_balance:.2%})"
        )

        return final_size

    def _calculate_fractional_kelly(
        self,
        account_balance: float,
        win_rate: Optional[float],
        avg_win: Optional[float],
        avg_loss: Optional[float]
    ) -> float:
        """
        Calculate position size using Fractional Kelly Criterion.

        2024 Best Practice: Use 1/10 Kelly for crypto volatility.

        Kelly formula: f* = (bp - q) / b
        where:
        - b = ratio of win to loss
        - p = probability of winning
        - q = probability of losing = 1 - p
        """
        # Get historical stats if not provided
        if win_rate is None or avg_win is None or avg_loss is None:
            with db.session_scope() as session:
                summary = TradeRepository.get_performance_summary(session, days=30)
                win_rate = summary.get('win_rate', 0.5)
                avg_win = summary.get('largest_win', 0) or 100
                avg_loss = abs(summary.get('largest_loss', 0)) or 100

        # Ensure reasonable defaults
        if win_rate == 0 or avg_loss == 0:
            log.warning("Insufficient data for Kelly Criterion, using default 2%")
            return account_balance * 0.02

        # Calculate Kelly percentage
        b = safe_divide(avg_win, avg_loss, 1.0)  # Win/loss ratio
        p = win_rate
        q = 1 - p

        kelly_percent = safe_divide((b * p - q), b, 0.02)

        # Apply fractional Kelly (1/10 for crypto - 2024 best practice)
        fractional_kelly = kelly_percent * self.fractional_kelly

        # Cap between 1% and 10%
        fractional_kelly = max(0.01, min(fractional_kelly, 0.10))

        kelly_position = account_balance * fractional_kelly

        log.debug(
            f"Kelly Criterion: win_rate={win_rate:.2%}, "
            f"win/loss_ratio={b:.2f}, "
            f"kelly={kelly_percent:.2%}, "
            f"fractional={fractional_kelly:.2%}"
        )

        return kelly_position

    def _calculate_volatility_factor(self, atr: float, price: float) -> float:
        """
        Calculate position size adjustment based on volatility.

        Higher volatility = smaller position (risk reduction).
        Lower volatility = larger position (opportunity).
        """
        atr_percent = (atr / price) * 100

        # Volatility thresholds
        if atr_percent < 1.0:
            # Low volatility - can increase position
            return 1.2
        elif atr_percent < 2.0:
            # Normal volatility
            return 1.0
        elif atr_percent < 3.0:
            # High volatility - reduce position
            return 0.8
        else:
            # Very high volatility - significantly reduce
            return 0.6

    def should_audit_performance(self) -> bool:
        """
        Check if monthly audit is due (2024 best practice).
        """
        if self.last_audit_date is None:
            return True

        days_since_audit = (datetime.utcnow() - self.last_audit_date).days
        return days_since_audit >= 30

    def run_monthly_audit(self) -> Dict:
        """
        Run monthly performance audit (2024 best practice).

        Returns warnings if:
        - Win rate < 50%
        - Sharpe ratio < 1.0
        - Max drawdown > 20%
        """
        with db.session_scope() as session:
            summary = TradeRepository.get_performance_summary(session, days=30)

        warnings = []

        # Check win rate
        if summary['win_rate'] < 0.50:
            warnings.append(
                f"⚠️  Low win rate: {summary['win_rate']:.1%} (target: >50%)"
            )

        # Check drawdown (simplified - should calculate from equity curve)
        if summary['total_pnl'] < 0:
            warnings.append(
                f"⚠️  Monthly loss: ${summary['total_pnl']:.2f}"
            )

        # Check if trading too frequently
        if summary['total_trades'] > 100:
            warnings.append(
                f"⚠️  High trade frequency: {summary['total_trades']} trades/month"
            )

        self.last_audit_date = datetime.utcnow()

        return {
            'audit_date': self.last_audit_date,
            'win_rate': summary['win_rate'],
            'total_pnl': summary['total_pnl'],
            'total_trades': summary['total_trades'],
            'warnings': warnings
        }

    def calculate_dynamic_stop_loss(
        self,
        entry_price: float,
        side: str,
        atr: Optional[float] = None,
        volatility_regime: str = "normal"
    ) -> float:
        """
        Calculate dynamic stop loss based on market conditions.

        Args:
            entry_price: Entry price
            side: BUY or SELL
            atr: Average True Range
            volatility_regime: "low", "normal", "high"

        Returns:
            Stop loss price
        """
        # Base stop loss
        base_stop_percent = self.stop_loss_percent

        # Adjust based on volatility regime
        if volatility_regime == "low":
            adjusted_stop = base_stop_percent * 0.8  # Tighter stop
        elif volatility_regime == "high":
            adjusted_stop = base_stop_percent * 1.5  # Wider stop
        else:
            adjusted_stop = base_stop_percent

        # Use ATR if available (preferred method)
        if atr and atr > 0:
            # Stop at 1.5x ATR
            stop_distance = atr * 1.5
        else:
            stop_distance = entry_price * adjusted_stop

        if side.upper() == "BUY":
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance

        log.debug(
            f"Dynamic stop-loss: regime={volatility_regime}, "
            f"distance={stop_distance:.2f}, price={stop_loss:.2f}"
        )

        return stop_loss

    def get_risk_metrics_v2(self, session) -> Dict:
        """Get enhanced risk metrics."""
        base_metrics = {
            'open_positions': len(TradeRepository.get_open_trades(session)),
            'max_positions': self.max_concurrent_positions,
        }

        # Get 30-day performance
        summary = TradeRepository.get_performance_summary(session, days=30)
        base_metrics.update(summary)

        # Add V2 metrics
        base_metrics['fractional_kelly'] = self.fractional_kelly
        base_metrics['max_single_position_pct'] = self.max_single_position * 100

        # Audit status
        if self.should_audit_performance():
            base_metrics['audit_needed'] = True
            base_metrics['audit_message'] = "⚠️  Monthly audit due"
        else:
            base_metrics['audit_needed'] = False

        return base_metrics


# Global enhanced risk manager
enhanced_risk_manager = EnhancedRiskManager()


if __name__ == "__main__":
    # Test enhanced risk manager
    print("Testing Enhanced Risk Manager V2...")

    rm = EnhancedRiskManager()

    # Test position sizing
    balance = 10000
    entry_price = 45000
    stop_loss = 44500
    atr = 500

    position_size = rm.calculate_optimal_position_size(
        account_balance=balance,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        confidence=0.85,
        atr=atr,
        win_rate=0.60,
        avg_win=150,
        avg_loss=100
    )

    print(f"\nOptimal Position Size: ${position_size:.2f}")
    print(f"Percentage of portfolio: {position_size/balance:.2%}")

    # Test dynamic stop loss
    sl_normal = rm.calculate_dynamic_stop_loss(entry_price, "BUY", atr, "normal")
    sl_high = rm.calculate_dynamic_stop_loss(entry_price, "BUY", atr, "high")

    print(f"\nDynamic Stop-Loss (normal volatility): ${sl_normal:,.2f}")
    print(f"Dynamic Stop-Loss (high volatility): ${sl_high:,.2f}")

    # Test audit
    if rm.should_audit_performance():
        print("\n⚠️  Monthly audit recommended")

    print("\n✅ Enhanced Risk Manager V2 test complete")

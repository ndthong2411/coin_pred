"""
Risk management engine for position sizing and risk control.
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from config import settings
from src.utils import log, calculate_position_size, safe_divide
from src.database import db, TradeRepository
import numpy as np


class RiskManager:
    """Manage trading risk and position sizing."""

    def __init__(self):
        """Initialize risk manager."""
        self.max_position_size = settings.trading.max_position_size
        self.max_daily_loss = settings.trading.max_daily_loss
        self.stop_loss_percent = settings.trading.stop_loss_percent
        self.take_profit_percent = settings.trading.take_profit_percent
        self.max_concurrent_positions = settings.trading.max_concurrent_positions

        log.info(f"Risk Manager initialized: Max position {self.max_position_size*100}%")

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        confidence: float = 1.0
    ) -> float:
        """
        Calculate optimal position size.

        Args:
            account_balance: Total account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            confidence: Model confidence (0-1)

        Returns:
            Position size in quote currency
        """
        # Base position size (% of portfolio)
        base_position = account_balance * self.max_position_size

        # Adjust by confidence
        adjusted_position = base_position * confidence

        # Kelly Criterion (optional, more aggressive)
        # kelly_fraction = self._calculate_kelly_criterion()
        # adjusted_position = min(adjusted_position, account_balance * kelly_fraction)

        # Risk-based position sizing
        risk_amount = account_balance * self.max_position_size
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk > 0:
            risk_based_size = risk_amount / price_risk
            adjusted_position = min(adjusted_position, risk_based_size * entry_price)

        log.debug(f"Position size: ${adjusted_position:.2f} (confidence: {confidence:.2%})")
        return adjusted_position

    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price
            side: BUY or SELL
            atr: Average True Range (optional, for dynamic stop)

        Returns:
            Stop loss price
        """
        if atr and atr > 0:
            # Dynamic stop loss based on ATR
            stop_distance = atr * 1.5
        else:
            # Fixed percentage stop loss
            stop_distance = entry_price * self.stop_loss_percent

        if side.upper() == "BUY":
            stop_loss = entry_price - stop_distance
        else:  # SELL/SHORT
            stop_loss = entry_price + stop_distance

        return stop_loss

    def calculate_take_profit(
        self,
        entry_price: float,
        side: str,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Entry price
            side: BUY or SELL
            risk_reward_ratio: Risk/reward ratio

        Returns:
            Take profit price
        """
        profit_distance = entry_price * self.take_profit_percent * risk_reward_ratio

        if side.upper() == "BUY":
            take_profit = entry_price + profit_distance
        else:  # SELL/SHORT
            take_profit = entry_price - profit_distance

        return take_profit

    def can_open_position(
        self,
        symbol: str,
        account_balance: float
    ) -> Tuple[bool, str]:
        """
        Check if we can open a new position.

        Args:
            symbol: Trading symbol
            account_balance: Current balance

        Returns:
            (can_trade, reason)
        """
        with db.session_scope() as session:
            # Check concurrent positions
            open_trades = TradeRepository.get_open_trades(session)
            if len(open_trades) >= self.max_concurrent_positions:
                return False, f"Max concurrent positions reached ({self.max_concurrent_positions})"

            # Check if already have position in this symbol
            symbol_trades = [t for t in open_trades if t.symbol == symbol]
            if symbol_trades:
                return False, f"Already have open position in {symbol}"

            # Check daily loss limit
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_pnl = self._get_daily_pnl(session, today)

            if daily_pnl < 0 and abs(daily_pnl) >= account_balance * self.max_daily_loss:
                return False, f"Daily loss limit reached (${abs(daily_pnl):.2f})"

        return True, "OK"

    def _get_daily_pnl(self, session, start_date: datetime) -> float:
        """Get total P/L for the day."""
        summary = TradeRepository.get_performance_summary(session, days=1)
        return summary.get('total_pnl', 0.0)

    def should_close_position(
        self,
        current_price: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        side: str
    ) -> Tuple[bool, str]:
        """
        Check if position should be closed.

        Args:
            current_price: Current market price
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            side: BUY or SELL

        Returns:
            (should_close, reason)
        """
        if side.upper() == "BUY":
            # Check stop loss
            if current_price <= stop_loss:
                return True, "Stop Loss"

            # Check take profit
            if current_price >= take_profit:
                return True, "Take Profit"

        else:  # SELL/SHORT
            # Check stop loss
            if current_price >= stop_loss:
                return True, "Stop Loss"

            # Check take profit
            if current_price <= take_profit:
                return True, "Take Profit"

        return False, ""

    def get_risk_metrics(self, session) -> Dict:
        """Get current risk metrics."""
        open_trades = TradeRepository.get_open_trades(session)
        summary = TradeRepository.get_performance_summary(session, days=30)

        return {
            'open_positions': len(open_trades),
            'max_positions': self.max_concurrent_positions,
            'total_trades_30d': summary.get('total_trades', 0),
            'win_rate_30d': summary.get('win_rate', 0),
            'total_pnl_30d': summary.get('total_pnl', 0),
            'avg_pnl_30d': summary.get('avg_pnl', 0),
        }

    def _calculate_kelly_criterion(self) -> float:
        """
        Calculate Kelly Criterion for position sizing.

        Returns:
            Optimal fraction of capital to risk
        """
        with db.session_scope() as session:
            summary = TradeRepository.get_performance_summary(session, days=30)

            win_rate = summary.get('win_rate', 0.5)
            avg_win = summary.get('largest_win', 0)
            avg_loss = abs(summary.get('largest_loss', 0))

            if avg_loss == 0:
                return 0.02  # Default 2%

            # Kelly formula: (bp - q) / b
            # b = ratio of win to loss
            # p = probability of winning
            # q = probability of losing = 1 - p

            b = safe_divide(avg_win, avg_loss, 1.0)
            p = win_rate
            q = 1 - p

            kelly = safe_divide((b * p - q), b, 0.02)

            # Apply fractional Kelly (more conservative)
            fractional_kelly = kelly * 0.5  # Use 50% of Kelly

            # Cap at reasonable limits
            return max(0.01, min(fractional_kelly, 0.1))  # Between 1% and 10%


# Global risk manager instance
risk_manager = RiskManager()


if __name__ == "__main__":
    # Test risk manager
    print("Testing Risk Manager...")

    rm = RiskManager()

    # Test position sizing
    balance = 10000
    entry_price = 45000
    stop_loss = 44500

    position_size = rm.calculate_position_size(balance, entry_price, stop_loss, confidence=0.85)
    print(f"\nPosition Size: ${position_size:.2f}")
    print(f"Percentage of portfolio: {position_size/balance:.2%}")

    # Test stop loss / take profit
    sl = rm.calculate_stop_loss(entry_price, "BUY")
    tp = rm.calculate_take_profit(entry_price, "BUY")

    print(f"\nEntry: ${entry_price:,.2f}")
    print(f"Stop Loss: ${sl:,.2f} ({(sl-entry_price)/entry_price:.2%})")
    print(f"Take Profit: ${tp:,.2f} ({(tp-entry_price)/entry_price:.2%})")

    # Test should close
    should_close, reason = rm.should_close_position(46000, entry_price, sl, tp, "BUY")
    print(f"\nAt price $46,000: Close={should_close}, Reason={reason}")

    print("\n✅ Risk Manager test complete")

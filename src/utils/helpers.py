"""
General utility helper functions.
"""
import pytz
from datetime import datetime, timedelta
from typing import Union, List, Dict, Any
import pandas as pd
import numpy as np
from config import settings


def get_current_time(timezone: str = None) -> datetime:
    """
    Get current time in specified timezone.

    Args:
        timezone: Timezone string (default from settings)

    Returns:
        Current datetime
    """
    tz = pytz.timezone(timezone or settings.system.timezone)
    return datetime.now(tz)


def convert_timezone(dt: datetime, from_tz: str = "UTC", to_tz: str = None) -> datetime:
    """
    Convert datetime from one timezone to another.

    Args:
        dt: Datetime object
        from_tz: Source timezone
        to_tz: Target timezone (default from settings)

    Returns:
        Converted datetime
    """
    if dt.tzinfo is None:
        dt = pytz.timezone(from_tz).localize(dt)
    target_tz = pytz.timezone(to_tz or settings.system.timezone)
    return dt.astimezone(target_tz)


def format_timestamp(timestamp: Union[int, float, datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp to string.

    Args:
        timestamp: Unix timestamp or datetime object
        format_str: Format string

    Returns:
        Formatted string
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
    else:
        dt = timestamp
    return dt.strftime(format_str)


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.

    Args:
        old_value: Original value
        new_value: New value

    Returns:
        Percentage change (e.g., 0.05 for 5% increase)
    """
    if old_value == 0:
        return 0.0
    return (new_value - old_value) / old_value


def round_to_precision(value: float, precision: int = 8) -> float:
    """
    Round value to specified decimal precision.

    Args:
        value: Value to round
        precision: Number of decimal places

    Returns:
        Rounded value
    """
    return round(value, precision)


def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float
) -> float:
    """
    Calculate position size based on risk management.

    Args:
        account_balance: Total account balance
        risk_percent: Risk percentage (e.g., 0.02 for 2%)
        entry_price: Entry price
        stop_loss_price: Stop loss price

    Returns:
        Position size
    """
    risk_amount = account_balance * risk_percent
    price_risk = abs(entry_price - stop_loss_price)
    if price_risk == 0:
        return 0.0
    position_size = risk_amount / price_risk
    return position_size


def calculate_profit_loss(
    entry_price: float,
    exit_price: float,
    quantity: float,
    side: str = "LONG"
) -> float:
    """
    Calculate profit/loss for a trade.

    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Position size
        side: Trade side (LONG or SHORT)

    Returns:
        Profit/loss amount
    """
    if side == "LONG":
        return (exit_price - entry_price) * quantity
    else:  # SHORT
        return (entry_price - exit_price) * quantity


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio.

    Args:
        returns: Series of returns
        risk_free_rate: Risk-free rate

    Returns:
        Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate
    return np.sqrt(252) * (excess_returns.mean() / excess_returns.std())  # Annualized


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    Calculate maximum drawdown.

    Args:
        equity_curve: Series of equity values

    Returns:
        Maximum drawdown (negative value)
    """
    if len(equity_curve) == 0:
        return 0.0

    cumulative_max = equity_curve.expanding().max()
    drawdown = (equity_curve - cumulative_max) / cumulative_max
    return drawdown.min()


def normalize_symbol(symbol: str) -> str:
    """
    Normalize trading symbol format.

    Args:
        symbol: Symbol in any format (BTC/USDT, BTCUSDT, etc.)

    Returns:
        Normalized symbol (BTC/USDT)
    """
    symbol = symbol.upper().replace("-", "").replace("_", "")
    if "/" not in symbol:
        # Try to split common pairs
        for quote in ["USDT", "BUSD", "USD", "BTC", "ETH"]:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
    return symbol


def denormalize_symbol(symbol: str) -> str:
    """
    Convert symbol to exchange format (remove /).

    Args:
        symbol: Normalized symbol (BTC/USDT)

    Returns:
        Exchange format (BTCUSDT)
    """
    return symbol.replace("/", "")


def validate_symbol(symbol: str, valid_symbols: List[str]) -> bool:
    """
    Validate if symbol is in the list of valid symbols.

    Args:
        symbol: Symbol to validate
        valid_symbols: List of valid symbols

    Returns:
        True if valid
    """
    normalized = normalize_symbol(symbol)
    return normalized in [normalize_symbol(s) for s in valid_symbols]


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split list into chunks of size n.

    Args:
        lst: List to split
        n: Chunk size

    Returns:
        List of chunks
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division with default value for division by zero.

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero

    Returns:
        Result or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_fees(amount: float, fee_rate: float = 0.001) -> float:
    """
    Calculate trading fees.

    Args:
        amount: Trade amount
        fee_rate: Fee rate (default 0.1%)

    Returns:
        Fee amount
    """
    return amount * fee_rate


def is_market_open() -> bool:
    """
    Check if crypto market is open (always true for crypto).

    Returns:
        True (crypto markets are 24/7)
    """
    return True


def sanitize_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def dict_to_query_string(params: Dict[str, Any]) -> str:
    """
    Convert dictionary to URL query string.

    Args:
        params: Dictionary of parameters

    Returns:
        Query string
    """
    return "&".join([f"{k}={v}" for k, v in params.items()])


if __name__ == "__main__":
    # Test helpers
    print("Testing helper functions...")

    # Test time functions
    print(f"Current time: {get_current_time()}")
    print(f"Formatted: {format_timestamp(datetime.now())}")

    # Test percentage change
    print(f"Percentage change (100 -> 105): {calculate_percentage_change(100, 105) * 100:.2f}%")

    # Test position sizing
    pos_size = calculate_position_size(10000, 0.02, 100, 95)
    print(f"Position size: {pos_size:.4f}")

    # Test symbol normalization
    print(f"Normalized: {normalize_symbol('BTCUSDT')}")
    print(f"Denormalized: {denormalize_symbol('BTC/USDT')}")

    # Test Sharpe ratio
    returns = pd.Series(np.random.randn(100) * 0.01)
    print(f"Sharpe ratio: {calculate_sharpe_ratio(returns):.2f}")

    print("✅ Helpers test complete")

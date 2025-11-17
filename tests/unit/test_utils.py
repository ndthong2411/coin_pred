"""
Unit tests for utility functions.
"""
import pytest

from src.utils.helpers import (
    denormalize_symbol,
    calculate_position_size,
    safe_divide,
    format_number
)


@pytest.mark.unit
class TestUtilityFunctions:
    """Test utility helper functions."""

    def test_denormalize_symbol(self):
        """Test symbol denormalization."""
        # Test various formats
        assert denormalize_symbol("BTC/USDT") == "BTCUSDT"
        assert denormalize_symbol("ETH/USDT") == "ETHUSDT"
        assert denormalize_symbol("BTC-USDT") == "BTCUSDT"

    def test_calculate_position_size(self):
        """Test position size calculation."""
        balance = 10000
        risk_percent = 0.02  # 2%

        position_size = calculate_position_size(balance, risk_percent)

        assert position_size == 200  # 2% of 10000
        assert position_size > 0

    def test_calculate_position_size_zero_risk(self):
        """Test position size with zero risk."""
        balance = 10000
        risk_percent = 0

        position_size = calculate_position_size(balance, risk_percent)

        assert position_size == 0

    def test_safe_divide(self):
        """Test safe division."""
        assert safe_divide(10, 2, default=0) == 5
        assert safe_divide(10, 0, default=0) == 0
        assert safe_divide(10, 0, default=999) == 999

    def test_safe_divide_none_values(self):
        """Test safe division with None values."""
        assert safe_divide(None, 5, default=0) == 0
        assert safe_divide(10, None, default=0) == 0

    def test_format_number(self):
        """Test number formatting."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"
        assert format_number(1234.5678, decimals=2) == "1,234.57"

    def test_format_number_negative(self):
        """Test formatting negative numbers."""
        assert format_number(-1000) == "-1,000"
        assert format_number(-1234.56, decimals=2) == "-1,234.56"

"""
Unit tests for Binance client.
"""
import pytest
from unittest.mock import patch, MagicMock

# Note: Binance client tests require mocking since we don't want to make real API calls


@pytest.mark.unit
class TestBinanceClient:
    """Test Binance client functionality."""

    @patch('src.data_collection.binance_client.Client')
    def test_get_price(self, mock_client):
        """Test getting current price."""
        from src.data_collection.binance_client import BinanceClient

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_symbol_ticker.return_value = {'price': '45000.00'}

        client = BinanceClient()
        price = client.get_price("BTC/USDT")

        assert isinstance(price, float)
        assert price > 0

    @patch('src.data_collection.binance_client.Client')
    def test_get_account_balance(self, mock_client):
        """Test getting account balance."""
        from src.data_collection.binance_client import BinanceClient

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_account.return_value = {
            'balances': [
                {'asset': 'USDT', 'free': '10000.00', 'locked': '0.00'},
                {'asset': 'BTC', 'free': '0.5', 'locked': '0.0'}
            ]
        }

        client = BinanceClient()
        balance = client.get_account_balance()

        assert isinstance(balance, dict)
        assert 'USDT' in balance
        assert balance['USDT'] > 0

    @patch('src.data_collection.binance_client.Client')
    def test_create_market_order(self, mock_client):
        """Test creating market order."""
        from src.data_collection.binance_client import BinanceClient

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.create_order.return_value = {
            'orderId': 12345,
            'status': 'FILLED',
            'executedQty': '0.01'
        }

        client = BinanceClient()
        order = client.create_market_order("BTC/USDT", "BUY", 0.01)

        assert 'orderId' in order
        assert order['status'] == 'FILLED'

    @patch('src.data_collection.binance_client.Client')
    def test_get_klines(self, mock_client):
        """Test getting historical klines."""
        from src.data_collection.binance_client import BinanceClient

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_klines.return_value = [
            [1609459200000, '29000', '29100', '28900', '29050', '100.5', 1609459260000, '2905000', 100, '50.25', '1452500', '0']
        ]

        client = BinanceClient()
        klines = client.get_klines("BTC/USDT", "1h", limit=100)

        assert isinstance(klines, list)
        assert len(klines) > 0

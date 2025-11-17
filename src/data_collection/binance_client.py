"""
Binance API client wrapper.
Provides unified interface for market data and trading operations.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import ccxt
from binance.client import Client as BinanceClient
from binance.exceptions import BinanceAPIException
from config import settings
from src.utils import log, retry_on_failure, rate_limit, denormalize_symbol, normalize_symbol
import pandas as pd


class BinanceAPIClient:
    """Wrapper for Binance API operations."""

    def __init__(self, testnet: bool = None):
        """
        Initialize Binance API client.

        Args:
            testnet: Use testnet (default from settings)
        """
        self.testnet = testnet if testnet is not None else settings.binance.testnet
        self.api_key = settings.binance.api_key
        self.api_secret = settings.binance.api_secret

        # Initialize python-binance client
        self.client = BinanceClient(
            self.api_key,
            self.api_secret,
            testnet=self.testnet,
        )

        # Initialize ccxt for additional features
        exchange_class = ccxt.binanceusdm if self.testnet else ccxt.binance
        self.ccxt_client = exchange_class({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })

        log.info(f"Binance client initialized (testnet={self.testnet})")

    @retry_on_failure(max_attempts=3)
    def ping(self) -> bool:
        """
        Test connectivity to Binance API.

        Returns:
            True if connected
        """
        try:
            self.client.ping()
            return True
        except Exception as e:
            log.error(f"Binance ping failed: {e}")
            return False

    @retry_on_failure(max_attempts=3)
    @rate_limit(calls=10, period=60)
    def get_server_time(self) -> datetime:
        """
        Get Binance server time.

        Returns:
            Server datetime
        """
        response = self.client.get_server_time()
        return datetime.fromtimestamp(response['serverTime'] / 1000)

    @retry_on_failure(max_attempts=3)
    def get_exchange_info(self, symbol: str = None) -> Dict[str, Any]:
        """
        Get exchange information.

        Args:
            symbol: Optional symbol filter

        Returns:
            Exchange info dict
        """
        info = self.client.get_exchange_info()
        if symbol:
            symbol_normalized = denormalize_symbol(symbol)
            for s in info['symbols']:
                if s['symbol'] == symbol_normalized:
                    return s
            return {}
        return info

    @retry_on_failure(max_attempts=3)
    @rate_limit(calls=10, period=60)
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get 24hr ticker price change statistics.

        Args:
            symbol: Trading symbol

        Returns:
            Ticker data
        """
        symbol_normalized = denormalize_symbol(symbol)
        return self.client.get_ticker(symbol=symbol_normalized)

    @retry_on_failure(max_attempts=3)
    @rate_limit(calls=10, period=60)
    def get_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Current price
        """
        symbol_normalized = denormalize_symbol(symbol)
        ticker = self.client.get_symbol_ticker(symbol=symbol_normalized)
        return float(ticker['price'])

    @retry_on_failure(max_attempts=3)
    @rate_limit(calls=5, period=60)
    def get_historical_klines(
        self,
        symbol: str,
        interval: str = '1m',
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data.

        Args:
            symbol: Trading symbol
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            start_time: Start datetime
            end_time: End datetime
            limit: Number of klines to retrieve (max 1000)

        Returns:
            DataFrame with OHLCV data
        """
        symbol_normalized = denormalize_symbol(symbol)

        # Convert datetime to milliseconds
        start_str = int(start_time.timestamp() * 1000) if start_time else None
        end_str = int(end_time.timestamp() * 1000) if end_time else None

        klines = self.client.get_historical_klines(
            symbol_normalized,
            interval,
            start_str=start_str,
            end_str=end_str,
            limit=limit,
        )

        # Convert to DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])

        # Convert types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        # Select main columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df.set_index('timestamp', inplace=True)

        log.debug(f"Retrieved {len(df)} klines for {symbol} ({interval})")
        return df

    @retry_on_failure(max_attempts=3)
    @rate_limit(calls=10, period=60)
    def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book depth.

        Args:
            symbol: Trading symbol
            limit: Depth limit (5, 10, 20, 50, 100, 500, 1000, 5000)

        Returns:
            Order book with bids and asks
        """
        symbol_normalized = denormalize_symbol(symbol)
        depth = self.client.get_order_book(symbol=symbol_normalized, limit=limit)

        return {
            'timestamp': datetime.utcnow(),
            'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
            'asks': [[float(price), float(qty)] for price, qty in depth['asks']],
        }

    @retry_on_failure(max_attempts=3)
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balances.

        Returns:
            Dict of asset balances
        """
        account = self.client.get_account()
        balances = {}

        for balance in account['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                balances[balance['asset']] = {
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                }

        return balances

    @retry_on_failure(max_attempts=3)
    def get_asset_balance(self, asset: str) -> float:
        """
        Get balance for specific asset.

        Args:
            asset: Asset symbol (e.g., 'USDT', 'BTC')

        Returns:
            Available balance
        """
        balance = self.client.get_asset_balance(asset=asset)
        return float(balance['free']) if balance else 0.0

    # Trading operations

    @retry_on_failure(max_attempts=2)
    def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> Dict[str, Any]:
        """
        Create market order.

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity

        Returns:
            Order response
        """
        symbol_normalized = denormalize_symbol(symbol)

        try:
            if side.upper() == 'BUY':
                order = self.client.order_market_buy(
                    symbol=symbol_normalized,
                    quantity=quantity
                )
            else:
                order = self.client.order_market_sell(
                    symbol=symbol_normalized,
                    quantity=quantity
                )

            log.info(f"Market order created: {side} {quantity} {symbol}")
            return order

        except BinanceAPIException as e:
            log.error(f"Market order failed: {e}")
            raise

    @retry_on_failure(max_attempts=2)
    def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> Dict[str, Any]:
        """
        Create limit order.

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price

        Returns:
            Order response
        """
        symbol_normalized = denormalize_symbol(symbol)

        try:
            if side.upper() == 'BUY':
                order = self.client.order_limit_buy(
                    symbol=symbol_normalized,
                    quantity=quantity,
                    price=str(price)
                )
            else:
                order = self.client.order_limit_sell(
                    symbol=symbol_normalized,
                    quantity=quantity,
                    price=str(price)
                )

            log.info(f"Limit order created: {side} {quantity} {symbol} @ {price}")
            return order

        except BinanceAPIException as e:
            log.error(f"Limit order failed: {e}")
            raise

    @retry_on_failure(max_attempts=2)
    def create_oco_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        stop_limit_price: float,
    ) -> Dict[str, Any]:
        """
        Create OCO (One-Cancels-Other) order for take-profit + stop-loss.

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            price: Take profit price
            stop_price: Stop loss trigger price
            stop_limit_price: Stop loss limit price

        Returns:
            Order response
        """
        symbol_normalized = denormalize_symbol(symbol)

        try:
            order = self.client.create_oco_order(
                symbol=symbol_normalized,
                side=side.upper(),
                quantity=quantity,
                price=str(price),
                stopPrice=str(stop_price),
                stopLimitPrice=str(stop_limit_price),
                stopLimitTimeInForce='GTC'
            )

            log.info(f"OCO order created: {side} {quantity} {symbol}")
            return order

        except BinanceAPIException as e:
            log.error(f"OCO order failed: {e}")
            raise

    @retry_on_failure(max_attempts=3)
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            symbol: Trading symbol
            order_id: Order ID

        Returns:
            Cancellation response
        """
        symbol_normalized = denormalize_symbol(symbol)

        try:
            result = self.client.cancel_order(
                symbol=symbol_normalized,
                orderId=order_id
            )
            log.info(f"Order cancelled: {order_id} for {symbol}")
            return result

        except BinanceAPIException as e:
            log.error(f"Cancel order failed: {e}")
            raise

    @retry_on_failure(max_attempts=3)
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Get order status.

        Args:
            symbol: Trading symbol
            order_id: Order ID

        Returns:
            Order info
        """
        symbol_normalized = denormalize_symbol(symbol)
        return self.client.get_order(symbol=symbol_normalized, orderId=order_id)

    @retry_on_failure(max_attempts=3)
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.

        Args:
            symbol: Optional symbol filter

        Returns:
            List of open orders
        """
        if symbol:
            symbol_normalized = denormalize_symbol(symbol)
            return self.client.get_open_orders(symbol=symbol_normalized)
        return self.client.get_open_orders()

    def get_trade_fee(self, symbol: str) -> float:
        """
        Get trading fee for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Fee rate (e.g., 0.001 for 0.1%)
        """
        # Binance default fee is 0.1%, with BNB discount 0.075%
        # This can be customized based on VIP level
        return 0.001  # 0.1%


# Global client instance
binance_client = BinanceAPIClient()


if __name__ == "__main__":
    # Test Binance client
    print("Testing Binance client...")

    # Test connectivity
    if binance_client.ping():
        print("✅ Binance API connected")
    else:
        print("❌ Binance API connection failed")

    # Test server time
    server_time = binance_client.get_server_time()
    print(f"Server time: {server_time}")

    # Test getting price
    try:
        price = binance_client.get_price("BTC/USDT")
        print(f"BTC/USDT price: ${price:,.2f}")
    except Exception as e:
        print(f"Error getting price: {e}")

    # Test historical data
    try:
        df = binance_client.get_historical_klines(
            "BTC/USDT",
            interval="1h",
            limit=10
        )
        print(f"\nHistorical data (last 10 hours):")
        print(df)
    except Exception as e:
        print(f"Error getting historical data: {e}")

    print("\n✅ Binance client test complete")

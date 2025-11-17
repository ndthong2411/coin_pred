"""
Trading executor - executes and manages trades.
"""
from typing import Dict, Optional
from datetime import datetime
from config import settings
from src.utils import log, log_trade, denormalize_symbol
from src.database import db, Trade, TradeRepository, TradeSide, OrderType, TradeStatus
from src.data_collection import binance_client
from .risk_manager import risk_manager
from src.utils.telegram_bot import telegram


class TradingExecutor:
    """Execute and manage trades."""

    def __init__(self, mode: str = "paper"):
        """
        Initialize trading executor.

        Args:
            mode: 'paper' or 'live'
        """
        self.mode = mode
        self.is_live = mode == "live"
        log.info(f"Trading Executor initialized in {mode.upper()} mode")

    def execute_signal(
        self,
        symbol: str,
        signal: Dict,
        account_balance: float
    ) -> Optional[Trade]:
        """
        Execute a trading signal.

        Args:
            symbol: Trading symbol
            signal: Signal dict from signal_generator
            account_balance: Current account balance

        Returns:
            Trade object if executed, None otherwise
        """
        action = signal['action']

        if action == "HOLD":
            return None

        # Check if we can open position
        can_trade, reason = risk_manager.can_open_position(symbol, account_balance)
        if not can_trade:
            log.warning(f"Cannot open position for {symbol}: {reason}")
            return None

        # Get current price
        current_price = signal.get('current_price') or binance_client.get_price(symbol)

        # Calculate position size
        stop_loss = risk_manager.calculate_stop_loss(current_price, action)
        position_size = risk_manager.calculate_position_size(
            account_balance,
            current_price,
            stop_loss,
            confidence=signal['confidence']
        )

        # Calculate quantity
        quantity = position_size / current_price

        # Calculate take profit
        take_profit = risk_manager.calculate_take_profit(current_price, action)

        # Execute trade
        if self.is_live:
            trade = self._execute_live_trade(
                symbol, action, quantity, current_price, stop_loss, take_profit
            )
        else:
            trade = self._execute_paper_trade(
                symbol, action, quantity, current_price, stop_loss, take_profit, signal
            )

        if trade:
            log_trade(action, symbol, price=current_price, quantity=quantity, confidence=signal['confidence'])

            # Send Telegram notification
            telegram.send_trade_execution(
                symbol=symbol,
                side=action,
                quantity=quantity,
                price=current_price,
                order_id=trade.entry_order_id
            )

        return trade

    def _execute_paper_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_loss: float,
        take_profit: float,
        signal: Dict
    ) -> Trade:
        """Execute paper trade (simulated)."""
        log.info(f"📝 PAPER TRADE: {side} {quantity:.6f} {symbol} @ ${price:,.2f}")

        # Create trade record
        with db.session_scope() as session:
            trade = TradeRepository.create(
                session,
                symbol=symbol,
                side=TradeSide.BUY if side == "BUY" else TradeSide.SELL,
                order_type=OrderType.MARKET,
                entry_price=price,
                quantity=quantity,
                entry_value=price * quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                entry_confidence=signal['confidence'],
                entry_order_id=f"PAPER_{datetime.utcnow().timestamp()}",
                notes=f"Paper trade - Reasons: {', '.join(signal['reasons'][:3])}"
            )

            log.info(f"Paper trade created: ID={trade.id}")
            return trade

    def _execute_live_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_loss: float,
        take_profit: float
    ) -> Optional[Trade]:
        """Execute live trade on Binance."""
        log.warning(f"🔴 LIVE TRADE: {side} {quantity:.6f} {symbol} @ ${price:,.2f}")

        try:
            # Place market order
            order = binance_client.create_market_order(symbol, side, quantity)

            log.info(f"Live order executed: {order['orderId']}")

            # Place OCO order for stop-loss and take-profit
            try:
                oco_order = binance_client.create_oco_order(
                    symbol=symbol,
                    side="SELL" if side == "BUY" else "BUY",
                    quantity=quantity,
                    price=take_profit,
                    stop_price=stop_loss,
                    stop_limit_price=stop_loss * 0.999  # Slightly below stop price
                )

                log.info(f"OCO order placed: {oco_order}")

            except Exception as e:
                log.error(f"Failed to place OCO order: {e}")

            # Create trade record
            with db.session_scope() as session:
                executed_price = float(order.get('fills', [{}])[0].get('price', price))
                executed_qty = float(order.get('executedQty', quantity))

                trade = TradeRepository.create(
                    session,
                    symbol=symbol,
                    side=TradeSide.BUY if side == "BUY" else TradeSide.SELL,
                    order_type=OrderType.MARKET,
                    entry_price=executed_price,
                    quantity=executed_qty,
                    entry_value=executed_price * executed_qty,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_order_id=str(order['orderId']),
                    stop_loss_order_id=str(oco_order.get('orderListId', '')) if oco_order else None
                )

                return trade

        except Exception as e:
            log.error(f"Failed to execute live trade: {e}")
            telegram.send_error(str(e), context=f"Live trade {side} {symbol}")
            return None

    def check_and_close_positions(self):
        """Check all open positions and close if needed."""
        with db.session_scope() as session:
            open_trades = TradeRepository.get_open_trades(session)

            for trade in open_trades:
                try:
                    self._check_position(trade, session)
                except Exception as e:
                    log.error(f"Error checking position {trade.id}: {e}")

    def _check_position(self, trade: Trade, session):
        """Check if position should be closed."""
        symbol = trade.symbol

        # Get current price
        current_price = binance_client.get_price(symbol)

        # Check if should close
        should_close, reason = risk_manager.should_close_position(
            current_price,
            trade.entry_price,
            trade.stop_loss,
            trade.take_profit,
            trade.side.value
        )

        if should_close:
            log.info(f"Closing position {trade.id}: {reason}")
            self.close_position(trade, current_price, reason, session)

    def close_position(
        self,
        trade: Trade,
        exit_price: float,
        reason: str,
        session
    ):
        """Close a position."""
        symbol = trade.symbol

        if self.is_live:
            # Execute close order on Binance
            try:
                side = "SELL" if trade.side == TradeSide.BUY else "BUY"
                order = binance_client.create_market_order(symbol, side, trade.quantity)

                log.info(f"Position closed on Binance: {order['orderId']}")

                exit_price = float(order.get('fills', [{}])[0].get('price', exit_price))
                trade.exit_order_id = str(order['orderId'])

                # Cancel OCO orders if any
                if trade.stop_loss_order_id:
                    try:
                        binance_client.cancel_order(symbol, int(trade.stop_loss_order_id))
                    except:
                        pass

            except Exception as e:
                log.error(f"Failed to close position on Binance: {e}")
                return

        # Update trade record
        TradeRepository.close_trade(session, trade.id, exit_price)

        # Calculate fees
        trade.fees = (trade.entry_value + trade.exit_value) * 0.001  # 0.1% each side

        trade.calculate_profit_loss()

        log_trade(
            "CLOSE",
            symbol,
            price=exit_price,
            profit=trade.net_profit_loss,
            reason=reason
        )

        # Send Telegram notification
        telegram.send_trade_closed(
            symbol=symbol,
            entry_price=trade.entry_price,
            exit_price=exit_price,
            quantity=trade.quantity,
            profit_loss=trade.net_profit_loss,
            profit_loss_percent=trade.profit_loss_percent,
            reason=reason
        )

        log.info(
            f"Position closed: {symbol} | "
            f"Entry: ${trade.entry_price:,.2f} | "
            f"Exit: ${exit_price:,.2f} | "
            f"P/L: ${trade.net_profit_loss:+,.2f} ({trade.profit_loss_percent:+.2%})"
        )


# Global trading executor (will be set by main.py)
trading_executor: Optional[TradingExecutor] = None


def set_trading_executor(mode: str):
    """Set global trading executor."""
    global trading_executor
    trading_executor = TradingExecutor(mode=mode)
    return trading_executor


if __name__ == "__main__":
    # Test trading executor
    print("Testing Trading Executor...")

    executor = TradingExecutor(mode="paper")

    # Sample signal
    signal = {
        'action': 'BUY',
        'confidence': 0.85,
        'current_price': 45000,
        'reasons': ['RSI oversold', 'MACD bullish', 'Strong uptrend']
    }

    # Execute
    trade = executor.execute_signal("BTC/USDT", signal, account_balance=10000)

    if trade:
        print(f"\n✅ Trade executed: {trade}")
        print(f"   Entry: ${trade.entry_price:,.2f}")
        print(f"   Stop Loss: ${trade.stop_loss:,.2f}")
        print(f"   Take Profit: ${trade.take_profit:,.2f}")
    else:
        print("\n⚠️  No trade executed")

    print("\n✅ Trading Executor test complete")

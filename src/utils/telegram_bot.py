"""
Telegram bot for alerts and notifications.
"""
import asyncio
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from config import settings
from .logger import log


class TelegramNotifier:
    """Send notifications via Telegram."""

    def __init__(self):
        """Initialize Telegram bot."""
        self.bot_token = settings.telegram.bot_token
        self.chat_id = settings.telegram.chat_id
        self.enabled = settings.telegram.enable_alerts and self.bot_token and self.chat_id
        self.bot: Optional[Bot] = None

        if self.enabled:
            self.bot = Bot(token=self.bot_token)
            log.info("Telegram bot initialized")
        else:
            log.warning("Telegram alerts disabled")

    async def _send_async(self, message: str, parse_mode: str = "HTML"):
        """Send message asynchronously."""
        if not self.enabled:
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            log.error(f"Telegram error: {e}")
            return False

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send message synchronously.

        Args:
            message: Message text
            parse_mode: HTML or Markdown

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            log.debug(f"Telegram disabled, would send: {message}")
            return False

        try:
            # Run async function in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._send_async(message, parse_mode))
            loop.close()
            return result
        except Exception as e:
            log.error(f"Error sending Telegram message: {e}")
            return False

    def send_startup_message(self):
        """Send bot startup notification."""
        message = (
            "🤖 <b>Trading Bot Started</b>\n\n"
            f"Mode: {settings.trading.trading_mode.upper()}\n"
            f"Symbols: {', '.join(settings.trading.target_symbols)}\n"
            f"Max Position: {settings.trading.max_position_size * 100}%\n"
            f"Stop Loss: {settings.trading.stop_loss_percent * 100}%\n"
            f"Take Profit: {settings.trading.take_profit_percent * 100}%"
        )
        self.send_message(message)

    def send_shutdown_message(self):
        """Send bot shutdown notification."""
        message = "🛑 <b>Trading Bot Stopped</b>"
        self.send_message(message)

    def send_trade_signal(
        self,
        symbol: str,
        action: str,
        price: float,
        confidence: float,
        reason: str = ""
    ):
        """Send trading signal notification."""
        emoji = "📈" if action == "BUY" else "📉" if action == "SELL" else "⏸️"

        message = (
            f"{emoji} <b>{action} Signal</b>\n\n"
            f"Symbol: {symbol}\n"
            f"Price: ${price:,.2f}\n"
            f"Confidence: {confidence:.1%}\n"
        )

        if reason:
            message += f"Reason: {reason}\n"

        self.send_message(message)

    def send_trade_execution(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str = None
    ):
        """Send trade execution notification."""
        emoji = "✅" if side == "BUY" else "💰"

        message = (
            f"{emoji} <b>Trade Executed</b>\n\n"
            f"Action: {side}\n"
            f"Symbol: {symbol}\n"
            f"Quantity: {quantity}\n"
            f"Price: ${price:,.2f}\n"
            f"Value: ${quantity * price:,.2f}\n"
        )

        if order_id:
            message += f"Order ID: {order_id}\n"

        self.send_message(message)

    def send_trade_closed(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        profit_loss: float,
        profit_loss_percent: float,
        reason: str = "Take Profit"
    ):
        """Send trade close notification."""
        is_profit = profit_loss > 0
        emoji = "🎉" if is_profit else "😔"

        message = (
            f"{emoji} <b>Trade Closed: {reason}</b>\n\n"
            f"Symbol: {symbol}\n"
            f"Entry: ${entry_price:,.2f}\n"
            f"Exit: ${exit_price:,.2f}\n"
            f"Quantity: {quantity}\n"
            f"P/L: ${profit_loss:+,.2f} ({profit_loss_percent:+.2%})\n"
        )

        self.send_message(message)

    def send_error(self, error_msg: str, context: str = ""):
        """Send error notification."""
        message = (
            f"❌ <b>Error Alert</b>\n\n"
            f"Error: {error_msg}\n"
        )

        if context:
            message += f"Context: {context}\n"

        self.send_message(message)

    def send_daily_summary(
        self,
        trades: int,
        wins: int,
        losses: int,
        total_pnl: float,
        win_rate: float
    ):
        """Send daily performance summary."""
        message = (
            f"📊 <b>Daily Summary</b>\n\n"
            f"Total Trades: {trades}\n"
            f"Wins: {wins} | Losses: {losses}\n"
            f"Win Rate: {win_rate:.1%}\n"
            f"Net P/L: ${total_pnl:+,.2f}\n"
        )

        self.send_message(message)

    def send_heartbeat(self):
        """Send heartbeat to confirm bot is running."""
        message = "💚 <b>Bot is running</b>"
        self.send_message(message)


# Global instance
telegram = TelegramNotifier()


if __name__ == "__main__":
    # Test Telegram bot
    print("Testing Telegram bot...")

    if telegram.enabled:
        telegram.send_message("🧪 <b>Test Message</b>\n\nThis is a test from the trading bot!")
        print("✅ Message sent! Check your Telegram.")
    else:
        print("⚠️  Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env")

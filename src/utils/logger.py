"""
Logging utility using loguru.
Provides structured logging with rotation and retention.
"""
import sys
from pathlib import Path
from loguru import logger
from config import settings


class Logger:
    """Custom logger wrapper around loguru."""

    def __init__(self):
        self._logger = logger
        self._setup_logger()

    def _setup_logger(self):
        """Configure logger with file and console handlers."""
        # Remove default handler
        self._logger.remove()

        # Console handler with colored output
        self._logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.system.log_level,
            colorize=True,
        )

        # File handler for all logs
        log_dir = settings.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        self._logger.add(
            log_dir / "app_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation=settings.system.log_rotation,
            retention=settings.system.log_retention,
            compression="zip",
            enqueue=True,  # Thread-safe
        )

        # Separate file for errors
        self._logger.add(
            log_dir / "errors_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            level="ERROR",
            rotation=settings.system.log_rotation,
            retention=settings.system.log_retention,
            compression="zip",
            enqueue=True,
        )

        # Trading-specific logs
        self._logger.add(
            log_dir / "trading_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="INFO",
            rotation="1 day",
            retention="90 days",
            compression="zip",
            filter=lambda record: "TRADE" in record["extra"],
            enqueue=True,
        )

    def get_logger(self):
        """Get the logger instance."""
        return self._logger

    @staticmethod
    def log_trade(action: str, symbol: str, **kwargs):
        """
        Log trading actions.

        Args:
            action: Action type (BUY, SELL, STOP_LOSS, etc.)
            symbol: Trading symbol
            **kwargs: Additional information
        """
        logger.bind(TRADE=True).info(
            f"TRADE | {action} | {symbol} | {kwargs}"
        )

    @staticmethod
    def log_model_prediction(symbol: str, prediction: str, confidence: float, **kwargs):
        """
        Log model predictions.

        Args:
            symbol: Trading symbol
            prediction: Prediction (UP/DOWN/NEUTRAL)
            confidence: Confidence score
            **kwargs: Additional information
        """
        logger.info(
            f"PREDICTION | {symbol} | {prediction} | Confidence: {confidence:.2%} | {kwargs}"
        )

    @staticmethod
    def log_error_with_context(error: Exception, context: dict):
        """
        Log error with additional context.

        Args:
            error: Exception object
            context: Dictionary with context information
        """
        logger.exception(
            f"Error occurred: {str(error)} | Context: {context}"
        )


# Global logger instance
log_instance = Logger()
log = log_instance.get_logger()


# Convenience functions
def log_trade(action: str, symbol: str, **kwargs):
    """Log trading action."""
    Logger.log_trade(action, symbol, **kwargs)


def log_prediction(symbol: str, prediction: str, confidence: float, **kwargs):
    """Log model prediction."""
    Logger.log_model_prediction(symbol, prediction, confidence, **kwargs)


def log_error(error: Exception, context: dict = None):
    """Log error with context."""
    Logger.log_error_with_context(error, context or {})


if __name__ == "__main__":
    # Test logging
    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")

    # Test trade logging
    log_trade("BUY", "BTC/USDT", price=45000, quantity=0.01, confidence=0.85)
    log_prediction("ETH/USDT", "UP", 0.78, model="ensemble")

    print("✅ Logging test complete. Check logs/ directory.")

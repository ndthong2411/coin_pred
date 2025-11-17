"""
Configuration management using Pydantic Settings.
Load from .env file and environment variables.
"""
from typing import List, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path


# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class BinanceConfig(BaseSettings):
    """Binance API configuration."""

    api_key: str = Field(default="", alias="BINANCE_API_KEY")
    api_secret: str = Field(default="", alias="BINANCE_API_SECRET")
    testnet: bool = Field(default=True, alias="BINANCE_TESTNET")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class TradingConfig(BaseSettings):
    """Trading strategy configuration."""

    trading_mode: Literal["paper", "live"] = Field(default="paper", alias="TRADING_MODE")
    max_position_size: float = Field(default=0.05, alias="MAX_POSITION_SIZE", ge=0.01, le=0.2)
    max_daily_loss: float = Field(default=0.05, alias="MAX_DAILY_LOSS", ge=0.01, le=0.2)
    stop_loss_percent: float = Field(default=0.005, alias="STOP_LOSS_PERCENT", ge=0.001, le=0.1)
    take_profit_percent: float = Field(default=0.01, alias="TAKE_PROFIT_PERCENT", ge=0.002, le=0.5)
    min_confidence_score: float = Field(default=0.70, alias="MIN_CONFIDENCE_SCORE", ge=0.5, le=0.99)
    target_symbols: List[str] = Field(
        default=["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"],
        alias="TARGET_SYMBOLS"
    )
    max_concurrent_positions: int = Field(default=3, ge=1, le=10)

    @field_validator("target_symbols", mode="before")
    @classmethod
    def parse_symbols(cls, v):
        """Parse comma-separated symbols."""
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    database_url: str = Field(
        default=f"sqlite:///{PROJECT_ROOT}/data/trading.db",
        alias="DATABASE_URL"
    )

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class TelegramConfig(BaseSettings):
    """Telegram bot configuration."""

    bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    enable_alerts: bool = Field(default=True, alias="ENABLE_TELEGRAM_ALERTS")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class TwitterConfig(BaseSettings):
    """Twitter API configuration."""

    api_key: str = Field(default="", alias="TWITTER_API_KEY")
    api_secret: str = Field(default="", alias="TWITTER_API_SECRET")
    access_token: str = Field(default="", alias="TWITTER_ACCESS_TOKEN")
    access_secret: str = Field(default="", alias="TWITTER_ACCESS_SECRET")
    bearer_token: str = Field(default="", alias="TWITTER_BEARER_TOKEN")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class RedditConfig(BaseSettings):
    """Reddit API configuration."""

    client_id: str = Field(default="", alias="REDDIT_CLIENT_ID")
    client_secret: str = Field(default="", alias="REDDIT_CLIENT_SECRET")
    user_agent: str = Field(default="CryptoTradingBot/1.0", alias="REDDIT_USER_AGENT")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class ExternalAPIConfig(BaseSettings):
    """External market data APIs configuration."""

    alpha_vantage_key: str = Field(default="", alias="ALPHA_VANTAGE_API_KEY")
    finnhub_key: str = Field(default="", alias="FINNHUB_API_KEY")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class ModelConfig(BaseSettings):
    """Machine learning model configuration."""

    retrain_days: int = Field(default=7, alias="MODEL_RETRAIN_DAYS", ge=1, le=30)
    feature_window_size: int = Field(default=60, alias="FEATURE_WINDOW_SIZE", ge=10, le=200)
    prediction_horizon: int = Field(default=15, alias="PREDICTION_HORIZON", ge=1, le=60)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class SystemConfig(BaseSettings):
    """System configuration."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", alias="LOG_LEVEL")
    log_rotation: str = Field(default="1 day", alias="LOG_ROTATION")
    log_retention: str = Field(default="30 days", alias="LOG_RETENTION")
    timezone: str = Field(default="UTC", alias="TIMEZONE")
    data_update_interval: int = Field(default=60, alias="DATA_UPDATE_INTERVAL", ge=1, le=3600)
    heartbeat_interval: int = Field(default=300, alias="HEARTBEAT_INTERVAL", ge=60, le=3600)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class Settings:
    """Main settings class combining all configurations."""

    def __init__(self):
        self.binance = BinanceConfig()
        self.trading = TradingConfig()
        self.database = DatabaseConfig()
        self.telegram = TelegramConfig()
        self.twitter = TwitterConfig()
        self.reddit = RedditConfig()
        self.external_api = ExternalAPIConfig()
        self.model = ModelConfig()
        self.system = SystemConfig()
        self.project_root = PROJECT_ROOT

        # Ensure data directories exist
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            PROJECT_ROOT / "data" / "raw",
            PROJECT_ROOT / "data" / "processed",
            PROJECT_ROOT / "data" / "models",
            PROJECT_ROOT / "logs",
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def validate_required_keys(self) -> List[str]:
        """
        Validate that required API keys are set.
        Returns list of missing keys.
        """
        missing = []

        if self.trading.trading_mode == "live":
            if not self.binance.api_key:
                missing.append("BINANCE_API_KEY")
            if not self.binance.api_secret:
                missing.append("BINANCE_API_SECRET")

        if self.telegram.enable_alerts:
            if not self.telegram.bot_token:
                missing.append("TELEGRAM_BOT_TOKEN (optional but recommended)")
            if not self.telegram.chat_id:
                missing.append("TELEGRAM_CHAT_ID (optional but recommended)")

        return missing

    def get_summary(self) -> str:
        """Get configuration summary."""
        return f"""
Configuration Summary:
=====================
Trading Mode: {self.trading.trading_mode.upper()}
Binance Testnet: {self.binance.testnet}
Target Symbols: {', '.join(self.trading.target_symbols)}
Max Position Size: {self.trading.max_position_size * 100}%
Stop Loss: {self.trading.stop_loss_percent * 100}%
Take Profit: {self.trading.take_profit_percent * 100}%
Min Confidence: {self.trading.min_confidence_score * 100}%
Database: {self.database.database_url}
Log Level: {self.system.log_level}
Telegram Alerts: {"Enabled" if self.telegram.enable_alerts else "Disabled"}
"""


# Global settings instance
settings = Settings()


if __name__ == "__main__":
    # Test configuration
    print(settings.get_summary())
    missing = settings.validate_required_keys()
    if missing:
        print("\n⚠️  Missing required configuration:")
        for key in missing:
            print(f"  - {key}")
    else:
        print("\n✅ All required configuration is set!")

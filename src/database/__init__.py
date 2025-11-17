"""Database package."""
from .connection import db, init_database, get_db
from .models import (
    Base,
    OHLCV,
    SentimentData,
    Feature,
    Prediction,
    Trade,
    PerformanceMetrics,
    SystemLog,
    TradeStatus,
    TradeSide,
    OrderType,
)
from .repository import (
    OHLCVRepository,
    SentimentRepository,
    FeatureRepository,
    PredictionRepository,
    TradeRepository,
    PerformanceRepository,
    SystemLogRepository,
)

__all__ = [
    # Connection
    "db",
    "init_database",
    "get_db",
    # Models
    "Base",
    "OHLCV",
    "SentimentData",
    "Feature",
    "Prediction",
    "Trade",
    "PerformanceMetrics",
    "SystemLog",
    "TradeStatus",
    "TradeSide",
    "OrderType",
    # Repositories
    "OHLCVRepository",
    "SentimentRepository",
    "FeatureRepository",
    "PredictionRepository",
    "TradeRepository",
    "PerformanceRepository",
    "SystemLogRepository",
]
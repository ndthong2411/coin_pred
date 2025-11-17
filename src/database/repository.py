"""
Repository pattern for database operations.
Provides high-level interface for data access.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session
from .models import (
    OHLCV,
    SentimentData,
    Feature,
    Prediction,
    Trade,
    PerformanceMetrics,
    SystemLog,
    TradeStatus,
    TradeSide,
)
from .connection import db
from src.utils import log
import pandas as pd


class OHLCVRepository:
    """Repository for OHLCV data."""

    @staticmethod
    def create(session: Session, **kwargs) -> OHLCV:
        """Create new OHLCV record."""
        ohlcv = OHLCV(**kwargs)
        session.add(ohlcv)
        return ohlcv

    @staticmethod
    def get_latest(session: Session, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Get latest OHLCV candles."""
        return (
            session.query(OHLCV)
            .filter(OHLCV.symbol == symbol, OHLCV.timeframe == timeframe)
            .order_by(desc(OHLCV.timestamp))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_range(
        session: Session,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[OHLCV]:
        """Get OHLCV data for a time range."""
        return (
            session.query(OHLCV)
            .filter(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp >= start_time,
                OHLCV.timestamp <= end_time,
            )
            .order_by(OHLCV.timestamp)
            .all()
        )

    @staticmethod
    def to_dataframe(ohlcv_list: List[OHLCV]) -> pd.DataFrame:
        """Convert OHLCV list to pandas DataFrame."""
        if not ohlcv_list:
            return pd.DataFrame()

        data = [
            {
                "timestamp": o.timestamp,
                "open": o.open,
                "high": o.high,
                "low": o.low,
                "close": o.close,
                "volume": o.volume,
            }
            for o in ohlcv_list
        ]
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    @staticmethod
    def bulk_insert(session: Session, ohlcv_list: List[Dict[str, Any]]):
        """Bulk insert OHLCV records."""
        session.bulk_insert_mappings(OHLCV, ohlcv_list)


class SentimentRepository:
    """Repository for sentiment data."""

    @staticmethod
    def create(session: Session, **kwargs) -> SentimentData:
        """Create new sentiment record."""
        sentiment = SentimentData(**kwargs)
        session.add(sentiment)
        return sentiment

    @staticmethod
    def get_latest(
        session: Session,
        symbol: str,
        source: Optional[str] = None,
        hours: int = 24,
    ) -> List[SentimentData]:
        """Get latest sentiment data."""
        since = datetime.utcnow() - timedelta(hours=hours)
        query = session.query(SentimentData).filter(
            SentimentData.symbol == symbol,
            SentimentData.timestamp >= since,
        )

        if source:
            query = query.filter(SentimentData.source == source)

        return query.order_by(desc(SentimentData.timestamp)).all()

    @staticmethod
    def get_average_sentiment(
        session: Session,
        symbol: str,
        hours: int = 24,
    ) -> float:
        """Calculate average sentiment score."""
        since = datetime.utcnow() - timedelta(hours=hours)
        result = session.query(func.avg(SentimentData.sentiment_score)).filter(
            SentimentData.symbol == symbol,
            SentimentData.timestamp >= since,
        ).scalar()

        return result or 0.0


class FeatureRepository:
    """Repository for feature data."""

    @staticmethod
    def create(session: Session, **kwargs) -> Feature:
        """Create new feature record."""
        feature = Feature(**kwargs)
        session.add(feature)
        return feature

    @staticmethod
    def get_latest(session: Session, symbol: str, timeframe: str, limit: int = 100) -> List[Feature]:
        """Get latest feature records."""
        return (
            session.query(Feature)
            .filter(Feature.symbol == symbol, Feature.timeframe == timeframe)
            .order_by(desc(Feature.timestamp))
            .limit(limit)
            .all()
        )

    @staticmethod
    def to_dataframe(features: List[Feature]) -> pd.DataFrame:
        """Convert features to DataFrame."""
        if not features:
            return pd.DataFrame()

        # Get all numeric columns
        data = []
        for f in features:
            row = {"timestamp": f.timestamp}
            for col in Feature.__table__.columns:
                if col.name not in ["id", "symbol", "timeframe", "created_at", "extra_features"]:
                    row[col.name] = getattr(f, col.name)
            data.append(row)

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df


class PredictionRepository:
    """Repository for predictions."""

    @staticmethod
    def create(session: Session, **kwargs) -> Prediction:
        """Create new prediction record."""
        prediction = Prediction(**kwargs)
        session.add(prediction)
        session.flush()  # To get the ID
        return prediction

    @staticmethod
    def get_latest(
        session: Session,
        symbol: str,
        model_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[Prediction]:
        """Get latest predictions."""
        query = session.query(Prediction).filter(Prediction.symbol == symbol)

        if model_name:
            query = query.filter(Prediction.model_name == model_name)

        return query.order_by(desc(Prediction.timestamp)).limit(limit).all()

    @staticmethod
    def get_accuracy(
        session: Session,
        model_name: str,
        days: int = 7,
    ) -> float:
        """
        Calculate model accuracy (simplified).
        In production, you'd compare predictions with actual outcomes.
        """
        # This is a placeholder - implement proper accuracy calculation
        # based on comparing predictions with actual price movements
        pass


class TradeRepository:
    """Repository for trades."""

    @staticmethod
    def create(session: Session, **kwargs) -> Trade:
        """Create new trade record."""
        trade = Trade(**kwargs)
        session.add(trade)
        session.flush()
        return trade

    @staticmethod
    def get_by_id(session: Session, trade_id: int) -> Optional[Trade]:
        """Get trade by ID."""
        return session.query(Trade).filter(Trade.id == trade_id).first()

    @staticmethod
    def get_open_trades(session: Session, symbol: Optional[str] = None) -> List[Trade]:
        """Get all open trades."""
        query = session.query(Trade).filter(Trade.status == TradeStatus.OPEN)
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.all()

    @staticmethod
    def get_closed_trades(
        session: Session,
        symbol: Optional[str] = None,
        days: Optional[int] = None,
    ) -> List[Trade]:
        """Get closed trades."""
        query = session.query(Trade).filter(Trade.status == TradeStatus.CLOSED)

        if symbol:
            query = query.filter(Trade.symbol == symbol)

        if days:
            since = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Trade.entry_time >= since)

        return query.order_by(desc(Trade.exit_time)).all()

    @staticmethod
    def close_trade(
        session: Session,
        trade_id: int,
        exit_price: float,
        exit_time: datetime = None,
    ) -> Trade:
        """Close a trade."""
        trade = TradeRepository.get_by_id(session, trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        trade.exit_time = exit_time or datetime.utcnow()
        trade.exit_price = exit_price
        trade.status = TradeStatus.CLOSED
        trade.calculate_profit_loss()

        return trade

    @staticmethod
    def get_performance_summary(session: Session, days: int = 30) -> Dict[str, Any]:
        """Get trading performance summary."""
        since = datetime.utcnow() - timedelta(days=days)
        trades = (
            session.query(Trade)
            .filter(Trade.status == TradeStatus.CLOSED, Trade.entry_time >= since)
            .all()
        )

        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
            }

        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.net_profit_loss and t.net_profit_loss > 0])
        losing_trades = len([t for t in trades if t.net_profit_loss and t.net_profit_loss < 0])
        total_pnl = sum([t.net_profit_loss for t in trades if t.net_profit_loss])
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "largest_win": max([t.net_profit_loss for t in trades if t.net_profit_loss], default=0),
            "largest_loss": min([t.net_profit_loss for t in trades if t.net_profit_loss], default=0),
        }


class PerformanceRepository:
    """Repository for performance metrics."""

    @staticmethod
    def create_or_update(session: Session, date: datetime, **kwargs) -> PerformanceMetrics:
        """Create or update performance metrics for a date."""
        metrics = session.query(PerformanceMetrics).filter(
            PerformanceMetrics.date == date.date()
        ).first()

        if metrics:
            for key, value in kwargs.items():
                setattr(metrics, key, value)
        else:
            metrics = PerformanceMetrics(date=date.date(), **kwargs)
            session.add(metrics)

        return metrics

    @staticmethod
    def get_latest(session: Session, days: int = 30) -> List[PerformanceMetrics]:
        """Get latest performance metrics."""
        since = datetime.utcnow() - timedelta(days=days)
        return (
            session.query(PerformanceMetrics)
            .filter(PerformanceMetrics.date >= since.date())
            .order_by(desc(PerformanceMetrics.date))
            .all()
        )


class SystemLogRepository:
    """Repository for system logs."""

    @staticmethod
    def create(session: Session, **kwargs) -> SystemLog:
        """Create system log entry."""
        log_entry = SystemLog(**kwargs)
        session.add(log_entry)
        return log_entry

    @staticmethod
    def get_recent(session: Session, level: Optional[str] = None, hours: int = 24, limit: int = 100):
        """Get recent system logs."""
        since = datetime.utcnow() - timedelta(hours=hours)
        query = session.query(SystemLog).filter(SystemLog.timestamp >= since)

        if level:
            query = query.filter(SystemLog.level == level)

        return query.order_by(desc(SystemLog.timestamp)).limit(limit).all()


if __name__ == "__main__":
    # Test repositories
    from .connection import init_database

    init_database()

    with db.session_scope() as session:
        # Test OHLCV repository
        ohlcv_repo = OHLCVRepository()
        ohlcv_repo.create(
            session,
            symbol="BTC/USDT",
            timeframe="1m",
            timestamp=datetime.utcnow(),
            open=45000,
            high=45100,
            low=44900,
            close=45050,
            volume=100,
        )

        # Test Trade repository
        trade_repo = TradeRepository()
        trade = trade_repo.create(
            session,
            symbol="BTC/USDT",
            side=TradeSide.BUY,
            order_type="market",
            entry_price=45000,
            quantity=0.01,
            entry_value=450,
        )

        print(f"✅ Created trade: {trade}")

    # Test retrieval
    with db.session_scope() as session:
        open_trades = TradeRepository.get_open_trades(session)
        print(f"Open trades: {len(open_trades)}")

        summary = TradeRepository.get_performance_summary(session)
        print(f"Performance summary: {summary}")

    print("✅ Repository test complete")

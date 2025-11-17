"""
FastAPI REST API Server for Trading Bot Control.
Provides programmatic access to bot functions and real-time data.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from src.database import db, init_database, TradeRepository, OHLCVRepository
from src.data_collection import binance_client
from src.utils import log

# Initialize FastAPI
app = FastAPI(
    title="Crypto Trading Bot API",
    description="REST API for controlling and monitoring the trading bot",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: str
    entry_price: float
    quantity: float
    status: str
    profit_loss: Optional[float]
    created_at: datetime


class PerformanceResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float
    largest_win: float
    largest_loss: float


class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: datetime
    change_24h: Optional[float]


class HealthResponse(BaseModel):
    status: str
    database: bool
    binance_api: bool
    timestamp: datetime


# Global bot state
bot_state = {
    'running': False,
    'mode': 'paper',
    'start_time': None
}


# Routes
@app.get("/", tags=["General"])
async def root():
    """API root endpoint."""
    return {
        "message": "Crypto Trading Bot API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "online"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """
    Health check endpoint.
    Returns system status.
    """
    # Check database
    db_status = db.check_connection()

    # Check Binance API
    try:
        api_status = binance_client.ping()
    except:
        api_status = False

    return HealthResponse(
        status="healthy" if db_status and api_status else "degraded",
        database=db_status,
        binance_api=api_status,
        timestamp=datetime.utcnow()
    )


@app.get("/status", tags=["Bot Control"])
async def get_bot_status():
    """Get current bot status."""
    return {
        "running": bot_state['running'],
        "mode": bot_state['mode'],
        "start_time": bot_state['start_time'],
        "uptime": str(datetime.utcnow() - bot_state['start_time']) if bot_state['start_time'] else None
    }


@app.post("/bot/start", tags=["Bot Control"])
async def start_bot(mode: str = "paper", background_tasks: BackgroundTasks = None):
    """
    Start the trading bot.

    Args:
        mode: 'paper' or 'live'
    """
    if bot_state['running']:
        raise HTTPException(status_code=400, detail="Bot is already running")

    if mode not in ['paper', 'live']:
        raise HTTPException(status_code=400, detail="Mode must be 'paper' or 'live'")

    # TODO: Actually start the bot in background
    bot_state['running'] = True
    bot_state['mode'] = mode
    bot_state['start_time'] = datetime.utcnow()

    log.info(f"Bot started via API in {mode} mode")

    return {
        "message": f"Bot started in {mode} mode",
        "status": "running"
    }


@app.post("/bot/stop", tags=["Bot Control"])
async def stop_bot():
    """Stop the trading bot."""
    if not bot_state['running']:
        raise HTTPException(status_code=400, detail="Bot is not running")

    # TODO: Actually stop the bot
    bot_state['running'] = False
    bot_state['start_time'] = None

    log.info("Bot stopped via API")

    return {
        "message": "Bot stopped",
        "status": "stopped"
    }


@app.get("/prices/{symbol}", response_model=PriceResponse, tags=["Market Data"])
async def get_price(symbol: str):
    """
    Get current price for a symbol.

    Args:
        symbol: Trading symbol (e.g., BTC/USDT)
    """
    try:
        price = binance_client.get_price(symbol)
        ticker = binance_client.get_ticker(symbol)

        return PriceResponse(
            symbol=symbol,
            price=price,
            timestamp=datetime.utcnow(),
            change_24h=float(ticker['priceChangePercent'])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prices", tags=["Market Data"])
async def get_all_prices():
    """Get current prices for all configured symbols."""
    prices = {}

    for symbol in settings.trading.target_symbols:
        try:
            price = binance_client.get_price(symbol)
            prices[symbol] = price
        except:
            prices[symbol] = None

    return {
        "symbols": prices,
        "timestamp": datetime.utcnow()
    }


@app.get("/trades", tags=["Trading"])
async def get_trades(
    symbol: Optional[str] = None,
    days: int = 7,
    status: Optional[str] = None
):
    """
    Get trade history.

    Args:
        symbol: Filter by symbol (optional)
        days: Number of days to look back (default: 7)
        status: Filter by status: 'open', 'closed', 'cancelled' (optional)
    """
    with db.session_scope() as session:
        if status == 'open':
            trades = TradeRepository.get_open_trades(session, symbol)
        else:
            trades = TradeRepository.get_closed_trades(session, symbol, days)

        trade_list = []
        for trade in trades:
            trade_list.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side.value,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'status': trade.status.value,
                'profit_loss': trade.net_profit_loss,
                'profit_loss_percent': trade.profit_loss_percent,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time
            })

        return {
            "trades": trade_list,
            "count": len(trade_list)
        }


@app.get("/performance", response_model=PerformanceResponse, tags=["Analytics"])
async def get_performance(days: int = 30):
    """
    Get performance metrics.

    Args:
        days: Number of days to analyze (default: 30)
    """
    with db.session_scope() as session:
        summary = TradeRepository.get_performance_summary(session, days=days)

        return PerformanceResponse(**summary)


@app.get("/ohlcv/{symbol}", tags=["Market Data"])
async def get_ohlcv(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100
):
    """
    Get OHLCV historical data.

    Args:
        symbol: Trading symbol
        timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles (max 1000)
    """
    try:
        df = binance_client.get_historical_klines(symbol, timeframe, limit=limit)

        data = []
        for timestamp, row in df.iterrows():
            data.append({
                'timestamp': timestamp.isoformat(),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            })

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config", tags=["Configuration"])
async def get_config():
    """Get current configuration."""
    return {
        "trading": {
            "mode": settings.trading.trading_mode,
            "symbols": settings.trading.target_symbols,
            "max_position_size": settings.trading.max_position_size,
            "stop_loss": settings.trading.stop_loss_percent,
            "take_profit": settings.trading.take_profit_percent,
            "min_confidence": settings.trading.min_confidence_score,
            "max_concurrent_positions": settings.trading.max_concurrent_positions
        },
        "system": {
            "log_level": settings.system.log_level,
            "data_update_interval": settings.system.data_update_interval,
            "heartbeat_interval": settings.system.heartbeat_interval
        }
    }


@app.get("/stats", tags=["Analytics"])
async def get_statistics():
    """Get comprehensive statistics."""
    with db.session_scope() as session:
        # Database stats
        db_stats = {
            'ohlcv_records': db.get_table_count('ohlcv'),
            'total_trades': db.get_table_count('trades'),
            'predictions': db.get_table_count('predictions'),
            'features': db.get_table_count('features')
        }

        # Performance
        performance = TradeRepository.get_performance_summary(session, days=30)

        # Open positions
        open_trades = TradeRepository.get_open_trades(session)

        return {
            "database": db_stats,
            "performance": performance,
            "open_positions": len(open_trades),
            "timestamp": datetime.utcnow()
        }


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    log.info("FastAPI server starting...")
    init_database()
    log.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    log.info("FastAPI server shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Crypto Trading Bot - Complete Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Getting Started](#getting-started)
6. [Project Structure](#project-structure)
7. [Usage](#usage)
8. [Architecture](#architecture)
9. [Development](#development)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

This is an automated cryptocurrency trading bot with machine learning predictions, technical analysis, and risk management. The bot supports:

- **Real-time data collection** from Binance
- **50+ technical indicators** for analysis
- **Machine learning predictions** (Classical ML + Deep Learning)
- **Automated trading** with risk management
- **Paper trading** for testing strategies
- **Live trading** on Binance
- **Performance monitoring** and dashboards

---

## System Requirements

### Hardware
- **CPU**: 4+ cores recommended (i5/Ryzen 5 or better)
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 100GB+ free space (SSD preferred)
- **GPU**: NVIDIA GPU recommended for deep learning (optional)
- **Internet**: Stable connection, 10Mbps+

### Software
- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.10, 3.11, or 3.12
- **Git**: For version control

### Binance Account
- Binance account (testnet for practice, real account for live trading)
- API keys with trading permissions

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/coin_pred.git
cd coin_pred
```

### Step 2: Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- Data handling: pandas, numpy
- Trading: ccxt, python-binance
- ML: scikit-learn, xgboost, lightgbm
- DL: tensorflow, pytorch
- Database: SQLAlchemy, PostgreSQL/SQLite
- Dashboard: streamlit, plotly
- And many more...

**Installation time**: 5-15 minutes depending on your internet speed.

### Step 4: Verify Installation

```bash
python scripts/health_check.py
```

This will check:
- ✅ Python dependencies
- ✅ Configuration
- ✅ Database connection
- ✅ Binance API access

---

## Configuration

### Step 1: Create .env File

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Step 2: Get Binance API Keys

#### For Testnet (Practice):
1. Go to [Binance Testnet](https://testnet.binance.vision/)
2. Login with GitHub/Gmail
3. Create API keys
4. Copy API Key and Secret

#### For Live Trading:
1. Go to [Binance](https://www.binance.com)
2. Login → Account → API Management
3. Create API Key with trading permissions
4. **Enable IP whitelist for security!**
5. Copy API Key and Secret

### Step 3: Edit .env File

Open `.env` in a text editor and configure:

```env
# Binance API
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=True  # False for live trading

# Trading Settings
TRADING_MODE=paper  # or 'live'
MAX_POSITION_SIZE=0.05  # 5% per trade
STOP_LOSS_PERCENT=0.005  # 0.5%
TAKE_PROFIT_PERCENT=0.01  # 1%
MIN_CONFIDENCE_SCORE=0.70  # 70%

# Target Coins
TARGET_SYMBOLS=BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,XRP/USDT

# Database (SQLite by default)
DATABASE_URL=sqlite:///data/trading.db

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ENABLE_TELEGRAM_ALERTS=False
```

### Step 4: Test Configuration

```bash
python scripts/health_check.py
```

Expected output:
```
✅ Configuration OK
✅ Database connection OK
✅ Binance API OK
✅ All dependencies installed
```

---

## Getting Started

### Step 1: Initialize Database

```bash
python scripts/init_db.py
```

This creates all necessary database tables.

### Step 2: Download Historical Data

```bash
# Download 30 days of 1-minute data for all configured symbols
python scripts/download_data.py --days 30 --interval 1m

# Download specific symbols
python scripts/download_data.py --symbols BTC/USDT,ETH/USDT --days 7 --interval 1h
```

Options:
- `--days N`: Number of days to download (default: 30)
- `--interval`: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
- `--symbols`: Comma-separated symbols

### Step 3: Run Health Check

```bash
python scripts/health_check.py
```

Verify everything is working before trading.

### Step 4: Start Paper Trading

```bash
python main.py --mode paper
```

This will:
- ✅ Connect to Binance
- ✅ Start real-time data collection
- ✅ Monitor market prices
- ✅ Calculate indicators
- ✅ Generate trading signals (simulated)

Press `Ctrl+C` to stop.

---

## Project Structure

```
coin_pred/
├── config/                     # Configuration
│   ├── config.py              # Settings management
│   └── __init__.py
│
├── src/
│   ├── data_collection/       # Data collection modules
│   │   ├── binance_client.py  # Binance API wrapper
│   │   ├── websocket_collector.py  # Real-time data
│   │   ├── historical_downloader.py  # Historical data
│   │   └── __init__.py
│   │
│   ├── database/              # Database layer
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── connection.py      # DB connection
│   │   ├── repository.py      # Data access layer
│   │   └── __init__.py
│   │
│   ├── feature_engineering/   # Technical indicators
│   │   ├── indicators.py      # 50+ indicators
│   │   └── __init__.py
│   │
│   ├── models/                # ML/DL models (TODO)
│   │   ├── classical/         # XGBoost, Random Forest
│   │   ├── deep_learning/     # LSTM, Transformer
│   │   └── ensemble/          # Model ensemble
│   │
│   ├── trading/               # Trading engine (TODO)
│   │   ├── executor.py        # Order execution
│   │   ├── risk_manager.py    # Risk management
│   │   └── strategy.py        # Trading strategies
│   │
│   ├── backtesting/           # Backtesting (TODO)
│   │   └── backtest_engine.py
│   │
│   ├── dashboard/             # Web dashboard (TODO)
│   │   └── app.py             # Streamlit app
│   │
│   └── utils/                 # Utilities
│       ├── logger.py          # Logging
│       ├── decorators.py      # Decorators
│       ├── helpers.py         # Helper functions
│       └── __init__.py
│
├── scripts/                   # Utility scripts
│   ├── init_db.py            # Initialize database
│   ├── download_data.py      # Download historical data
│   └── health_check.py       # System health check
│
├── data/                      # Data storage
│   ├── raw/                  # Raw data
│   ├── processed/            # Processed data
│   └── models/               # Trained models
│
├── logs/                      # Log files
│
├── tests/                     # Test suite
│
├── .env                       # Configuration (YOU CREATE THIS)
├── .env.example              # Configuration template
├── .gitignore               # Git ignore
├── main.py                  # Main entry point
├── requirements.txt         # Dependencies
├── README.md               # Quick start
├── GUIDE.md                # This file
└── pyproject.toml          # Project config
```

---

## Usage

### Basic Commands

#### 1. Paper Trading (Simulated)
```bash
python main.py --mode paper
```
Safe for testing, no real money involved.

#### 2. Live Trading (CAUTION!)
```bash
python main.py --mode live
```
**WARNING**: Uses real money!

#### 3. Health Check
```bash
python scripts/health_check.py
```
Verify system status.

#### 4. Download Data
```bash
python scripts/download_data.py --days 30
```
Get historical data for training.

#### 5. Dashboard (TODO)
```bash
streamlit run src/dashboard/app.py
```
View performance metrics and charts.

### Advanced Usage

#### Custom Symbols
```bash
python main.py --mode paper --symbols BTC/USDT,ETH/USDT
```

#### Backtesting (TODO)
```bash
python scripts/backtest.py --start 2024-01-01 --end 2024-12-31
```

---

## Architecture

### Data Flow

```
1. DATA COLLECTION
   ├── Binance WebSocket → Real-time prices
   ├── Historical API → Past data
   └── External APIs → News, sentiment

2. FEATURE ENGINEERING
   ├── Technical Indicators (50+)
   ├── Sentiment Scores
   └── Market Correlations

3. PREDICTION
   ├── Classical ML (XGBoost, RF)
   ├── Deep Learning (LSTM, Transformer)
   └── Ensemble (Weighted average)

4. SIGNAL GENERATION
   ├── Buy/Sell/Hold signals
   ├── Confidence scores
   └── Position sizing

5. RISK MANAGEMENT
   ├── Stop-loss placement
   ├── Take-profit targets
   ├── Position size limits
   └── Daily loss limits

6. EXECUTION
   ├── Order placement
   ├── Order monitoring
   └── Position management

7. MONITORING
   ├── Performance metrics
   ├── Logs
   └── Telegram alerts
```

### Technologies

- **Language**: Python 3.10+
- **Data**: Pandas, NumPy
- **Trading**: CCXT, python-binance
- **Database**: SQLAlchemy + SQLite/PostgreSQL
- **ML**: scikit-learn, XGBoost, LightGBM
- **DL**: TensorFlow, PyTorch
- **Dashboard**: Streamlit, Plotly
- **API**: FastAPI (for external API)
- **Testing**: pytest
- **CI/CD**: GitHub Actions

---

## Development

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality
```bash
# Format code
black src/ tests/ config/

# Lint
flake8 src/ tests/ config/

# Type check
mypy src/ config/

# Sort imports
isort src/ tests/ config/
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Adding New Features

1. Create feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Write code + tests

3. Run tests and quality checks:
   ```bash
   pytest
   black src/
   flake8 src/
   ```

4. Commit and push:
   ```bash
   git add .
   git commit -m "Add my feature"
   git push origin feature/my-feature
   ```

5. Create Pull Request

---

## Troubleshooting

### Common Issues

#### 1. "Module not found" Error
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

#### 2. "Binance API connection failed"
**Possible causes**:
- Wrong API keys → Check `.env` file
- Network issues → Check internet connection
- API rate limit → Wait a few minutes

**Solution**:
```bash
# Test connection
python -c "from src.data_collection import binance_client; print(binance_client.ping())"
```

#### 3. "Database connection failed"
**Solution**: Re-initialize database
```bash
python scripts/init_db.py
```

#### 4. "Insufficient balance" (Live trading)
**Solution**: Deposit funds to Binance account or reduce `MAX_POSITION_SIZE` in `.env`

#### 5. WebSocket disconnects
**Solution**: The bot automatically reconnects. Check internet stability.

#### 6. High memory usage
**Solution**:
- Reduce `TARGET_SYMBOLS` count
- Increase `DATA_UPDATE_INTERVAL`
- Close other applications

### Getting Help

1. **Check logs**: `logs/app_YYYY-MM-DD.log`
2. **Run health check**: `python scripts/health_check.py`
3. **GitHub Issues**: Report bugs
4. **Discussions**: Ask questions

---

## Safety Guidelines

### NEVER:
- ❌ Share your API keys
- ❌ Commit `.env` to Git
- ❌ Start live trading without testing
- ❌ Trade more than you can afford to lose
- ❌ Leave bot running unmonitored

### ALWAYS:
- ✅ Start with paper trading
- ✅ Use testnet for development
- ✅ Set stop-losses
- ✅ Monitor the bot regularly
- ✅ Keep API keys secure
- ✅ Enable IP whitelist on Binance
- ✅ Start with small amounts

### Risk Warning

⚠️ **Cryptocurrency trading involves substantial risk of loss. This bot is provided as-is with no guarantees. You are responsible for all trading decisions and outcomes. Never invest more than you can afford to lose.**

---

## Next Steps

Now that you have the bot running, you can:

1. **Collect Data**: Let it run for a few days to collect market data
2. **Train Models**: Implement and train ML models (TODO)
3. **Backtest**: Test strategies on historical data (TODO)
4. **Paper Trade**: Run in paper mode for 1-2 weeks
5. **Monitor Performance**: Track win rate, profit, drawdown
6. **Optimize**: Tune parameters based on results
7. **Live Trading**: Start with small amounts

Good luck! 🚀

---

## Changelog

### Version 0.1.0 (Current)
- ✅ Project structure
- ✅ Configuration system
- ✅ Database models
- ✅ Binance API integration
- ✅ Real-time data collection (WebSocket)
- ✅ Historical data downloader
- ✅ Technical indicators (50+)
- ✅ Logging system
- ✅ Health check script
- ⏳ ML models (TODO)
- ⏳ Trading engine (TODO)
- ⏳ Dashboard (TODO)

---

**Happy Trading! 📈**

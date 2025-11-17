# Crypto Trading Bot 🤖

Automated cryptocurrency trading bot with machine learning predictions, sentiment analysis, and risk management.

## Features

### ✅ IMPLEMENTED (Phase 1-3)
- ✅ **Real-time Data Collection**: Binance WebSocket integration for live market data
- ✅ **Technical Indicators**: 50+ technical indicators (RSI, MACD, Bollinger Bands, ATR, etc.)
- ✅ **Machine Learning**: XGBoost price classifier with confidence scoring
- ✅ **Risk Management**: Kelly Criterion position sizing, dynamic stop-loss/take-profit
- ✅ **Signal Generation**: Multi-strategy ensemble (Technical + Trend + Mean Reversion + Momentum)
- ✅ **Paper Trading**: Fully functional simulated trading
- ✅ **Live Trading**: Real order execution on Binance with safety checks
- ✅ **Monitoring Dashboard**: Streamlit dashboard with real-time metrics
- ✅ **Telegram Alerts**: Full integration for trade notifications, signals, errors, heartbeats
- ✅ **Database**: Complete data models for OHLCV, trades, predictions, performance
- ✅ **Automated Trading**: End-to-end pipeline from data → signal → execution → monitoring

### ⏳ TODO (Phase 4+)
- ⏳ **Sentiment Analysis**: Twitter, Reddit, news sentiment tracking (models ready, API integration pending)
- ⏳ **Deep Learning**: LSTM, GRU, Transformer models for advanced predictions
- ⏳ **Backtesting Framework**: Comprehensive historical strategy testing
- ⏳ **Advanced Ensemble**: Combine XGBoost + LSTM + Sentiment for ultimate predictions

## 🚀 Quick Start

**👉 See [QUICKSTART.md](QUICKSTART.md) for detailed 5-minute setup guide!**

### Super Quick (TL;DR)

```bash
# 1. Install
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure (edit .env with your Binance API keys)
notepad .env

# 3. Initialize
python scripts/init_db.py
python scripts/download_data.py --days 7

# 4. Run Paper Trading
python main_enhanced.py --mode paper

# 5. View Dashboard (optional, in new terminal)
streamlit run src/dashboard/app.py
```

### Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Binance API keys** ([Testnet](https://testnet.binance.vision/) for practice)
- **16GB+ RAM** (8GB minimum)
- **NVIDIA GPU** (optional, for model training - auto-detected)

5. Initialize database:
```bash
python scripts/init_db.py
```

6. Download historical data:
```bash
python scripts/download_data.py
```

7. Train models (optional - pre-trained models included):
```bash
python scripts/train_models.py
```

8. Start the bot:
```bash
# Paper trading mode
python main.py --mode paper

# Live trading mode (use with caution!)
python main.py --mode live
```

## Project Structure

```
coin_pred/
├── config/                 # Configuration files
│   └── config.py          # Settings management
├── src/
│   ├── data_collection/   # Data collection modules
│   ├── feature_engineering/  # Feature engineering
│   ├── models/            # ML/DL models
│   ├── trading/           # Trading execution
│   ├── backtesting/       # Backtesting engine
│   ├── dashboard/         # Monitoring dashboard
│   └── utils/             # Utility functions
├── data/
│   ├── raw/               # Raw market data
│   ├── processed/         # Processed features
│   └── models/            # Trained models
├── logs/                  # Application logs
├── tests/                 # Test suite
└── scripts/               # Utility scripts
```

## Configuration

Edit `.env` file to configure:

- **Binance API**: Your API keys
- **Trading Parameters**: Position size, stop-loss, take-profit
- **Target Symbols**: Which coins to trade
- **Model Settings**: Retraining frequency, prediction horizon
- **Telegram**: Bot token for alerts

See `.env.example` for all available options.

## Usage Examples

### Paper Trading
```bash
python main.py --mode paper --symbols BTC/USDT,ETH/USDT
```

### Backtesting
```bash
python scripts/backtest.py --start 2024-01-01 --end 2024-12-31
```

### Dashboard
```bash
streamlit run src/dashboard/app.py
```

## Safety & Risk Management

⚠️ **IMPORTANT**: Cryptocurrency trading involves significant risk. This bot is provided as-is with no guarantees.

- Start with paper trading
- Test thoroughly before live trading
- Use small amounts initially
- Set strict stop-losses
- Never risk more than you can afford to lose
- Monitor the bot regularly

## Performance Metrics

The bot tracks:
- Win rate
- Total return
- Sharpe ratio
- Maximum drawdown
- Average profit per trade
- Profit factor

## Testing

Run tests:
```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=src --cov-report=html
```

## Development

### Code Quality

We use:
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **isort**: Import sorting
- **Pre-commit**: Git hooks

Setup pre-commit hooks:
```bash
pre-commit install
```

### CI/CD

GitHub Actions runs:
- Code quality checks
- Tests on Python 3.10, 3.11, 3.12
- Security vulnerability scans

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred from using this bot.

## Support

- 📖 Documentation: See `GUIDE.md` for detailed guide
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/coin_pred/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-username/coin_pred/discussions)

## Acknowledgments

- Binance API
- ccxt library
- scikit-learn, XGBoost, TensorFlow/PyTorch
- All open-source contributors

---

**Happy Trading! 🚀**

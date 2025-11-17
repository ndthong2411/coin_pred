# Crypto Trading Bot 🤖

Automated cryptocurrency trading bot with machine learning predictions, sentiment analysis, and risk management.

## Features

- ✅ **Real-time Data Collection**: Binance WebSocket integration for live market data
- ✅ **Sentiment Analysis**: Twitter, Reddit, and news sentiment tracking
- ✅ **Technical Indicators**: 50+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- ✅ **Machine Learning**: Classical ML (XGBoost, Random Forest) + Deep Learning (LSTM, Transformer)
- ✅ **Ensemble Predictions**: Combine multiple models for better accuracy
- ✅ **Risk Management**: Dynamic position sizing, stop-loss, take-profit
- ✅ **Backtesting**: Historical strategy testing
- ✅ **Paper Trading**: Test strategies without real money
- ✅ **Live Trading**: Automated trading on Binance
- ✅ **Monitoring Dashboard**: Real-time performance tracking
- ✅ **Telegram Alerts**: Get notified of trades and system status

## Quick Start

### Prerequisites

- Python 3.10+
- Binance API keys (for live trading)
- NVIDIA GPU (optional, for faster model training)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/coin_pred.git
cd coin_pred
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

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

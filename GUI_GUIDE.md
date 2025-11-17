# Desktop GUI Application Guide

## 🖥️ Crypto Trading Bot - Desktop Edition

Professional desktop application với PyQt5 cho real-time crypto trading.

---

## ✨ Features

### 1. **📊 Dashboard Tab**
- Real-time cryptocurrency prices
- 24h price changes với color coding
- Volume, High/Low tracking
- Auto-refresh mỗi 2 giây

### 2. **🤖 Trading Control Tab**
- Start/Stop bot (Paper hoặc Live mode)
- Bot status indicator (Running/Stopped)
- Uptime tracking
- Manual trade execution
- Activity log với timestamps

### 3. **📈 Live Monitoring Tab**
- Real-time open positions tracking
- Unrealized P/L calculation
- Performance metrics dashboard:
  - Total P/L
  - Win Rate
  - Total Trades
  - Open Positions count
- Color-coded profit/loss indicators

### 4. **📜 Trade History Tab**
- Complete trade history với filtering:
  - Filter by symbol
  - Filter by time period (days)
  - Filter by profitability
- Detailed trade information:
  - Entry/Exit prices
  - P/L in $ and %
  - Confidence scores
  - Trade duration
- Export to CSV functionality
- Summary statistics

### 5. **📉 Charts Tab**
- Real-time candlestick charts
- Volume bars (green/red based on trend)
- Multiple timeframes: 1m, 5m, 15m, 1h, 4h, 1d
- Multiple symbols
- Interactive zooming and panning
- Auto-refresh capability

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate

# Install PyQt5 and dependencies
pip install PyQt5==5.15.10 pyqtgraph==0.13.3 qtawesome==1.3.0

# Or install all from requirements
pip install -r requirements.txt
```

### 2. Run Desktop App

```bash
python main_gui.py
```

**That's it!** 🎉

---

## 🎯 Usage Guide

### Starting the Bot

1. Open **Trading Control** tab
2. Select mode:
   - **Paper Trading**: Simulated trades (recommended for testing)
   - **Live Trading**: Real money (requires confirmation)
3. Click **▶️ Start Bot**
4. Bot status will show 🟢 RUNNING

### Monitoring Trades

1. Go to **Live Monitoring** tab
2. View open positions in real-time
3. Monitor unrealized P/L
4. Check performance metrics

### Viewing History

1. Go to **Trade History** tab
2. Select filters:
   - Symbol (or "All")
   - Days to look back
   - Profitability filter
3. Click **🔄 Refresh**
4. Export to CSV if needed

### Viewing Charts

1. Go to **Charts** tab
2. Select:
   - Symbol
   - Timeframe
3. Click **🔄 Refresh**
4. Interact with chart:
   - Zoom: Mouse wheel
   - Pan: Click and drag
   - Reset: Right-click → View All

---

## 🎨 UI Features

### Color Coding

- **Green**: Profits, Buy orders, Positive changes
- **Red**: Losses, Sell orders, Negative changes
- **Blue**: Neutral information
- **Gray**: Inactive/Stopped status

### Performance

- **Non-blocking UI**: All data loading happens in background threads
- **Smooth updates**: No freezing or lag
- **Real-time refresh**: Prices update every 2 seconds
- **Efficient rendering**: Uses pyqtgraph for fast charts

### Responsive Design

- Resizable windows
- Auto-adjusting columns
- Scrollable tables
- Tabbed interface for organization

---

## ⚙️ Technical Details

### Architecture

```
main_gui.py                    # Entry point
├── src/gui/
│   ├── main_window.py        # Main application window
│   ├── workers.py            # Background workers (QThread)
│   └── widgets/
│       ├── price_widget.py   # Real-time prices
│       ├── trading_panel.py  # Bot controls
│       ├── monitoring_widget.py  # Live monitoring
│       ├── history_widget.py     # Trade history
│       └── chart_widget.py       # Charts
```

### Background Workers

All workers run in separate threads để không block UI:

1. **PriceUpdateWorker**: Updates prices every 2 seconds
2. **OpenPositionsWorker**: Monitors open positions every 5 seconds
3. **PerformanceWorker**: Calculates performance metrics
4. **SystemStatsWorker**: Updates system statistics every 10 seconds
5. **TradeHistoryWorker**: Loads trade history on demand
6. **ChartDataWorker**: Loads chart data on demand

### Performance Optimization

- **QThread**: Prevents UI freezing
- **pyqtgraph**: 10-100x faster than matplotlib for real-time plots
- **Efficient updates**: Only updates changed data
- **Signal/Slot pattern**: Decoupled communication
- **Lazy loading**: Data loaded only when needed

---

## 🔧 Advanced Features

### Keyboard Shortcuts

- **F5**: Refresh all data
- **Ctrl+Q**: Quit application

### Menu Options

- **File** → Refresh All: Reload all data
- **File** → Exit: Close application
- **Tools** → Settings: Configuration (coming soon)
- **Help** → About: Application information

### Status Bar

Bottom status bar shows:
- Current bot status
- Database statistics
- Error messages
- Success notifications

---

## 📊 Performance Metrics Explained

### Win Rate
```
Win Rate = (Winning Trades / Total Trades) × 100%
```
- **Good**: >55%
- **Very Good**: >60%
- **Excellent**: >65%

### Total P/L
Total profit/loss across all trades
- **Green**: Profitable
- **Red**: Loss

### Sharpe Ratio (Coming Soon)
Risk-adjusted return measure
- **>1.0**: Acceptable
- **>1.5**: Good
- **>2.0**: Excellent

### Max Drawdown (Coming Soon)
Maximum peak-to-trough decline
- **<15%**: Good
- **<10%**: Very Good
- **<5%**: Excellent

---

## 🐛 Troubleshooting

### App doesn't start

```bash
# Check PyQt5 installation
python -c "from PyQt5.QtWidgets import QApplication; print('OK')"

# Reinstall if needed
pip install --force-reinstall PyQt5==5.15.10
```

### "No module named PyQt5"

```bash
pip install PyQt5==5.15.10 PyQt5-Qt5==5.15.2 PyQt5-sip==12.13.0
```

### Prices not updating

- Check internet connection
- Check Binance API keys in `.env`
- Check logs: `logs/app_YYYY-MM-DD.log`

### Charts not loading

- Check database has OHLCV data
- Run: `python scripts/download_data.py --days 7`
- Click Refresh button in Charts tab

### High CPU usage

- Close unused tabs
- Increase update intervals in workers
- Reduce number of symbols

---

## 💡 Tips & Best Practices

1. **Start with Paper Trading**
   - Test bot for 1-2 weeks
   - Review performance metrics
   - Adjust parameters

2. **Monitor Regularly**
   - Check open positions daily
   - Review trade history weekly
   - Export CSV for analysis

3. **Use Filters**
   - Filter by profitable trades to see what works
   - Filter by symbol to analyze individual pairs
   - Adjust time periods for different insights

4. **Export Data**
   - Export trade history regularly
   - Analyze in Excel/Google Sheets
   - Track long-term performance

5. **Keep Updated**
   - Pull latest code updates
   - Check OPTIMIZATIONS.md for improvements
   - Review logs for errors

---

## 🔒 Security Notes

### API Keys
- Stored in `.env` (never committed to git)
- Only trading permissions enabled
- IP whitelist recommended

### Live Trading
- Requires explicit confirmation
- Shows warning dialog
- Logs all actions

### Data Privacy
- All data stored locally
- SQLite database in `data/trading.db`
- No data sent to third parties

---

## 🎓 Next Steps

1. **Customize Settings**
   - Edit `config/config.py`
   - Adjust risk parameters
   - Add/remove symbols

2. **Train Models**
   ```bash
   python scripts/train_models.py
   ```

3. **Download More Data**
   ```bash
   python scripts/download_data.py --days 30
   ```

4. **Setup Telegram Alerts**
   - See QUICKSTART.md for instructions
   - Get notifications on your phone

5. **Monitor Performance**
   - Use Desktop App daily
   - Check Streamlit dashboard: `streamlit run src/dashboard/app_v2.py`
   - Review REST API: `python src/api/server.py`

---

## 📞 Support

- **Logs**: Check `logs/` directory
- **Database**: `data/trading.db`
- **Configuration**: `config/config.py`
- **Documentation**: README.md, GUIDE.md, OPTIMIZATIONS.md

---

## 🎉 Enjoy Trading!

The desktop app provides professional-grade monitoring and control for your crypto trading bot.

**Features Summary:**
- ✅ Real-time price monitoring
- ✅ One-click bot control
- ✅ Live position tracking
- ✅ Comprehensive trade history
- ✅ Interactive charts
- ✅ Export capabilities
- ✅ Professional UI/UX
- ✅ Non-blocking performance

**Happy Trading! 🚀📈💰**

---

**Version**: 2.0
**Last Updated**: 2025-01-17
**Status**: Production Ready ✅

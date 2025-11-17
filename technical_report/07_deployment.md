# 7. Deployment Guide

## Overview

Complete guide for deploying the crypto trading bot from development to production.

---

## Development Setup

### 1. Prerequisites

**Required:**
- Python 3.10+ (3.11 recommended)
- Git
- pip, virtualenv

**Optional:**
- VS Code or PyCharm
- Binance account (for live trading)
- Telegram bot (for notifications)

---

### 2. Initial Setup

```bash
# Clone repository
git clone https://github.com/your-username/coin_pred.git
cd coin_pred

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Configuration

#### Create `.env` file

```bash
# Copy template
cp .env.example .env

# Edit with your values
# Windows
notepad .env

# Linux/Mac
nano .env
```

#### `.env` contents:

```bash
# Binance API (Required)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=True  # True for testnet, False for live

# Trading Mode
TRADING_MODE=paper  # paper or live

# Database
DATABASE_URL=sqlite:///./data/trading.db

# Telegram (Optional but recommended)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
ENABLE_TELEGRAM_ALERTS=True

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

### 4. Initialize Database

```bash
python scripts/init_db.py
```

**Expected output:**
```
✅ Database initialized successfully
✅ Tables created: ohlcv, trades, predictions, features, performance_metrics, system_logs
```

---

### 5. Download Initial Data

```bash
# Quick test (7 days)
python scripts/download_data.py --days 7 --interval 1h

# Production (30 days)
python scripts/download_data.py --days 30 --interval 1m
```

**Expected output:**
```
Downloading BTC/USDT... [============================] 100%
✅ Downloaded 720 candles
✅ Data saved to database
```

---

### 6. Health Check

```bash
python scripts/health_check.py
```

**Expected output:**
```
🔍 Running system health check...

✅ Configuration OK
✅ Database OK (Connected, 720 OHLCV records)
✅ Binance API OK (BTC/USDT: $45,000.50)
✅ Dependencies OK (All packages installed)

🎉 All systems operational!
```

---

### 7. Train ML Model (Optional)

```bash
python scripts/train_models.py --interval 1h --horizon 6
```

**Expected output:**
```
Training XGBoost classifier...
Training samples: 600, Test samples: 120
✅ Training complete!
   Accuracy: 64.5%

Top 5 Features:
   rsi_14              : 0.1234
   macd                : 0.0987
   bb_pct              : 0.0856
   close_sma_5         : 0.0723
   volume_ratio        : 0.0654

💾 Model saved to: data/models/BTC_USDT_1h.pkl
```

---

## Running the Bot

### Paper Trading (Recommended First)

```bash
python main_enhanced.py --mode paper
```

**What happens:**
1. Bot starts
2. Connects to Binance (testnet or live API for data)
3. Starts WebSocket for real-time prices
4. Analyzes market every 10 iterations
5. Generates trading signals
6. **Simulates** trades (saves to DB only)
7. Monitors positions
8. Sends Telegram alerts (if configured)

**To stop:** Press `Ctrl+C`

---

### Desktop GUI

```bash
# Windows
start_gui.bat

# Linux/Mac
./start_gui.sh

# Or manually
python main_gui.py
```

**Features:**
- Real-time price monitoring
- One-click start/stop
- Live position tracking
- Trade history viewer
- Interactive charts

---

### Web Dashboard (Streamlit)

```bash
# In a separate terminal
streamlit run src/dashboard/app_v2.py
```

**Access:** http://localhost:8501

---

### REST API

```bash
# In a separate terminal
python src/api/server.py
```

**Access:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## Live Trading

**⚠️ CAUTION: Use real money!**

### Pre-requisites

1. ✅ Paper trading tested for 1-2 weeks
2. ✅ Win rate > 55%
3. ✅ Understand all risks
4. ✅ Only use money you can afford to lose
5. ✅ API keys from Binance (live account)
6. ✅ IP whitelist configured on Binance

### Steps

1. **Update `.env`:**
```bash
BINANCE_TESTNET=False  # Use live API
TRADING_MODE=live
```

2. **Verify configuration:**
```bash
python scripts/health_check.py
```

3. **Start bot:**
```bash
python main_enhanced.py --mode live
```

4. **Confirmation prompt:**
```
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
WARNING: YOU ARE ABOUT TO START LIVE TRADING!
This will use REAL MONEY on your Binance account.
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

Type 'YES I UNDERSTAND' to continue:
```

5. **Monitor carefully:**
- Watch desktop GUI
- Check Telegram alerts
- Review logs regularly

---

## Production Deployment

### Option 1: VPS Deployment

**Recommended VPS specs:**
- **CPU:** 2+ cores
- **RAM:** 4GB+
- **Storage:** 20GB+
- **OS:** Ubuntu 20.04 LTS or later
- **Network:** Stable, low latency to Binance servers

**Providers:**
- DigitalOcean ($12/month)
- Vultr ($10/month)
- Linode ($12/month)
- AWS EC2 t3.medium

#### Setup Steps

```bash
# 1. SSH to VPS
ssh user@your-vps-ip

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip git -y

# 4. Clone repository
git clone https://github.com/your-username/coin_pred.git
cd coin_pred

# 5. Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Configure .env
nano .env
# (paste your configuration)

# 8. Initialize database
python scripts/init_db.py

# 9. Download data
python scripts/download_data.py --days 30 --interval 1m

# 10. Test
python scripts/health_check.py
```

#### Run as Background Service (systemd)

Create service file:

```bash
sudo nano /etc/systemd/system/crypto-bot.service
```

Contents:

```ini
[Unit]
Description=Crypto Trading Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/coin_pred
Environment="PATH=/home/your-username/coin_pred/venv/bin"
ExecStart=/home/your-username/coin_pred/venv/bin/python main_enhanced.py --mode live
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot

# Check status
sudo systemctl status crypto-bot

# View logs
sudo journalctl -u crypto-bot -f
```

---

### Option 2: Docker Deployment

#### Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Initialize database on first run
RUN python scripts/init_db.py

# Expose API port (if using)
EXPOSE 8000

# Run bot
CMD ["python", "main_enhanced.py", "--mode", "paper"]
```

#### Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  trading-bot:
    build: .
    container_name: crypto-bot
    environment:
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      - BINANCE_API_SECRET=${BINANCE_API_SECRET}
      - TRADING_MODE=paper
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  dashboard:
    build: .
    container_name: crypto-dashboard
    command: streamlit run src/dashboard/app_v2.py
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  api:
    build: .
    container_name: crypto-api
    command: uvicorn src.api.server:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

#### Run

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f trading-bot

# Stop
docker-compose down
```

---

## Monitoring

### 1. Logs

**Location:**
```
logs/
├── app_2025-01-17.log       # All logs
├── trading_2025-01-17.log   # Trading only
└── error_2025-01-17.log     # Errors only
```

**View live:**
```bash
# All logs
tail -f logs/app_$(date +%Y-%m-%d).log

# Errors only
tail -f logs/error_$(date +%Y-%m-%d).log

# Trading events only
grep "Trade" logs/trading_$(date +%Y-%m-%d).log
```

---

### 2. Telegram Alerts

**Setup:**

1. Create bot with @BotFather
2. Get token
3. Get your chat ID from @userinfobot
4. Update `.env`
5. Test: `python -c "from src.utils import telegram; telegram.send_message('Test')"`

**Alert Types:**
- Trade executions
- Trade closures
- Errors
- Daily summaries
- Heartbeats (every hour)

---

### 3. Performance Metrics

**Daily:**
```bash
python -c "
from src.database import db, TradeRepository
with db.session_scope() as session:
    summary = TradeRepository.get_performance_summary(session, days=1)
    print(summary)
"
```

**Monthly:**
```bash
# Use dashboard or API
curl http://localhost:8000/performance?days=30
```

---

## Backup Strategy

### 1. Database Backups

**Manual backup:**
```bash
# Create backup
mkdir -p data/backups
cp data/trading.db data/backups/trading_$(date +%Y%m%d_%H%M%S).db

# Restore from backup
cp data/backups/trading_20250117_120000.db data/trading.db
```

**Automated backup (cron):**

```bash
# Edit crontab
crontab -e

# Add line (backup every day at 2am)
0 2 * * * cd /path/to/coin_pred && cp data/trading.db data/backups/trading_$(date +\%Y\%m\%d).db

# Keep only last 30 days
0 3 * * * find /path/to/coin_pred/data/backups -name "trading_*.db" -mtime +30 -delete
```

---

### 2. Configuration Backups

```bash
# Backup .env (exclude from git)
cp .env .env.backup

# Backup to encrypted storage
gpg -c .env  # Creates .env.gpg

# Restore
gpg .env.gpg  # Decrypts to .env
```

---

## Troubleshooting

### Bot won't start

```bash
# Check configuration
python scripts/health_check.py

# Check logs
cat logs/error_*.log

# Test API connection
python -c "from src.data_collection import binance_client; print(binance_client.ping())"
```

### No trades being executed

**Possible causes:**

1. **Low confidence:**
   - Check `settings.trading.min_confidence_score`
   - Lower threshold or improve signals

2. **Max positions reached:**
   - Check `settings.trading.max_concurrent_positions`
   - Close existing positions or increase limit

3. **Daily loss limit:**
   - Check `settings.trading.max_daily_loss`
   - Wait for next day or increase limit

4. **Insufficient data:**
   - Download more historical data
   - Check database: `SELECT COUNT(*) FROM ohlcv;`

### High CPU/Memory usage

```bash
# Check resource usage
top
htop  # if installed

# Reduce update frequency
# Edit workers interval in src/gui/workers.py
# Or reduce symbols in config
```

### WebSocket disconnects frequently

**Causes:**
- Network instability
- Firewall blocking
- Rate limiting

**Solutions:**
- Check network
- Whitelist Binance IPs
- Reduce number of symbols
- Increase reconnect delay

---

## Maintenance

### Daily Tasks

- [ ] Check Telegram alerts
- [ ] Review logs for errors
- [ ] Verify bot is running
- [ ] Check win rate

### Weekly Tasks

- [ ] Review performance metrics
- [ ] Analyze losing trades
- [ ] Adjust parameters if needed
- [ ] Update models if necessary
- [ ] Check database size

### Monthly Tasks

- [ ] Full performance review
- [ ] Backup database
- [ ] Update dependencies
- [ ] Review and optimize strategy
- [ ] Retrain ML models with new data

---

## Security Best Practices

### 1. API Keys

- ✅ Use API keys with **trading permissions ONLY**
- ✅ Never enable withdrawal permissions
- ✅ Enable IP whitelist on Binance
- ✅ Rotate keys periodically
- ✅ Never commit `.env` to git

### 2. VPS Security

```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw allow 22  # SSH
sudo ufw allow 8000  # API (if needed)
sudo ufw enable

# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use SSH keys instead of passwords
ssh-keygen -t ed25519
# Copy public key to VPS
```

### 3. Code Security

- Keep dependencies updated
- Review code before deployment
- Use environment variables for secrets
- Enable logging for audit trail

---

## Scaling

### Horizontal Scaling

**Multiple symbols:**
- Run separate instances per symbol
- Use different databases or schemas

**Multiple strategies:**
- Run multiple bots with different configs
- Compare performance

### Vertical Scaling

**Better VPS:**
- More CPU for faster analysis
- More RAM for larger datasets
- SSD for faster database

**Database upgrade:**
- SQLite → PostgreSQL
- Better concurrent access
- Advanced queries

---

## Next Steps

**After deployment:**

1. Monitor for 1-2 weeks (paper trading)
2. Review performance metrics
3. Adjust parameters based on results
4. Consider live trading if performance good
5. Start with small capital
6. Scale gradually

**Continuous improvement:**

- Collect more data
- Retrain models regularly
- Test new strategies
- Monitor market conditions
- Adapt parameters

---

**Completed!** Back to: [Index](./README.md)

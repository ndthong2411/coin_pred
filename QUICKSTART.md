# Quick Start Guide - Crypto Trading Bot

Hướng dẫn nhanh để chạy bot trong 5 phút!

## 🚀 Bước 1: Cài đặt (5-10 phút)

### Windows:

```cmd
# 1. Tạo virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Lưu ý:** Với máy của bạn (i9-12900K + RTX 3090), TensorFlow sẽ tự động detect CUDA.

## ⚙️ Bước 2: Cấu hình API Keys (2 phút)

### Lấy Binance API Keys:

**Cho Testnet (Khuyến nghị để test):**
1. Vào https://testnet.binance.vision/
2. Login bằng GitHub/Gmail
3. Generate API Key
4. Copy Key và Secret

**Cho Live Trading:**
1. Vào https://www.binance.com → API Management
2. Create API Key
3. Enable "Spot Trading" permission
4. **BẮT BUỘC:** Set IP Whitelist cho bảo mật
5. Copy Key và Secret

### Cấu hình .env:

```cmd
# File .env đã được tạo sẵn, edit nó:
notepad .env
```

Điền thông tin:
```env
# Binance API
BINANCE_API_KEY=paste_your_key_here
BINANCE_API_SECRET=paste_your_secret_here
BINANCE_TESTNET=True  # True cho testnet, False cho live

# Telegram (Optional nhưng khuyến nghị)
TELEGRAM_BOT_TOKEN=your_bot_token  # Lấy từ @BotFather
TELEGRAM_CHAT_ID=your_chat_id      # Lấy từ @userinfobot
ENABLE_TELEGRAM_ALERTS=True
```

## 📊 Bước 3: Khởi tạo Database (30 giây)

```cmd
python scripts\init_db.py
```

Expected output:
```
✅ Database tables created successfully
✅ Database connection successful
```

## 📥 Bước 4: Download Dữ liệu (5-10 phút)

### Cách 1: Download ít data để test nhanh
```cmd
python scripts\download_data.py --days 7 --interval 1h
```

### Cách 2: Download nhiều data để train model tốt hơn
```cmd
python scripts\download_data.py --days 30 --interval 1m
```

Expected output:
```
Downloading BTC/USDT... [====] 100%
✅ Data download complete!
```

## ✅ Bước 5: Health Check (10 giây)

```cmd
python scripts\health_check.py
```

Expected output:
```
✅ Configuration OK
✅ Database OK
✅ Binance API OK (BTC/USDT: $45,000)
✅ All dependencies installed
🎉 All systems operational!
```

## 🤖 Bước 6: Chạy Bot Paper Trading (BẮT ĐẦU!)

```cmd
python main_enhanced.py --mode paper
```

Bot sẽ:
- ✅ Kết nối Binance API
- ✅ Start WebSocket real-time data
- ✅ Hiển thị giá các coin realtime
- ✅ Phân tích kỹ thuật mỗi 10 vòng lặp
- ✅ Tạo trading signals
- ✅ Thực hiện paper trades (giả lập)
- ✅ Gửi alerts qua Telegram (nếu configured)
- ✅ Log mọi thứ vào `logs/`

**Output mẫu:**
```
🤖 CRYPTO TRADING BOT - PAPER MODE
✅ All systems initialized successfully!
🚀 Starting trading bot...
📡 Starting real-time data collection...

--- Analyzing BTC/USDT @ 14:35:00 ---
Current Price: $45,123.50
Signal: BUY (confidence: 78.5%)
Reasons: RSI oversold, MACD bullish, Strong uptrend
✅ Trade executed: ID=1
📝 PAPER TRADE: BUY 0.011000 BTC/USDT @ $45,123.50
```

**Nhấn Ctrl+C để dừng.**

## 📊 Bước 7: Xem Dashboard (OPTIONAL)

Mở terminal mới:

```cmd
streamlit run src\dashboard\app.py
```

Dashboard sẽ mở tại: http://localhost:8501

Features:
- 📊 Performance overview (Win rate, P/L)
- 💰 Trade history
- 📉 Price charts (candlestick)
- ⚙️ System status

## 🧠 Bước 8: Train ML Model (OPTIONAL)

```cmd
python scripts\train_models.py --interval 1h --horizon 6
```

Model sẽ:
- ✅ Load data từ database
- ✅ Calculate 50+ indicators
- ✅ Train XGBoost classifier
- ✅ Show accuracy & feature importance
- ✅ Save model tại `data/models/`

**Output mẫu:**
```
Training XGBoost classifier...
Training samples: 800, Test samples: 200
✅ Training complete!
   Accuracy: 64.5%

Top 10 Features:
   rsi_14              : 0.1234
   macd                : 0.0987
   bb_pct              : 0.0856
   ...

💾 Model saved to: data/models/BTC_USDT_1h.pkl
```

## 📱 Setup Telegram Alerts (OPTIONAL nhưng khuyến nghị)

### 1. Tạo Telegram Bot:
1. Mở Telegram, chat với @BotFather
2. Send `/newbot`
3. Đặt tên bot (vd: My Trading Bot)
4. Copy token (dạng: `123456:ABC-DEF1234...`)

### 2. Lấy Chat ID:
1. Chat với @userinfobot
2. Send bất kỳ message nào
3. Bot sẽ reply với Chat ID của bạn
4. Copy Chat ID

### 3. Update .env:
```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
ENABLE_TELEGRAM_ALERTS=True
```

### 4. Test:
```cmd
python -c "from src.utils import telegram; telegram.send_message('✅ Test message!')"
```

Check Telegram, bạn sẽ nhận message!

## 🔥 Chế độ LIVE TRADING (CẨN THẬN!)

⚠️ **CHỈ SỬ DỤNG SAU KHI:**
- ✅ Test paper trading ít nhất 1-2 tuần
- ✅ Win rate >55%
- ✅ Hiểu rõ rủi ro
- ✅ Chỉ dùng số tiền có thể chấp nhận mất

```cmd
python main_enhanced.py --mode live
```

Bot sẽ yêu cầu xác nhận:
```
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
WARNING: YOU ARE ABOUT TO START LIVE TRADING!
This will use REAL MONEY on your Binance account.
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

Type 'YES I UNDERSTAND' to continue:
```

## 📖 Tài liệu đầy đủ

- **README.md**: Tổng quan
- **GUIDE.md**: Hướng dẫn chi tiết (500+ lines)
- **Code documentation**: Inline trong source code

## 🆘 Troubleshooting

### Lỗi "Module not found"
```cmd
pip install -r requirements.txt
```

### Lỗi "Binance API connection failed"
- Check API keys trong `.env`
- Check internet connection
- Nếu dùng testnet, đảm bảo `BINANCE_TESTNET=True`

### Lỗi "Database connection failed"
```cmd
python scripts\init_db.py
```

### Bot không tạo trades
- Check logs: `logs/app_YYYY-MM-DD.log`
- Có thể confidence thấp (< 70%)
- Có thể market đang sideways (HOLD signal)
- Check dashboard để xem signals

### Health check failed
```cmd
python scripts\health_check.py
```
Sẽ show chi tiết lỗi ở đâu.

## 💡 Tips

1. **Bắt đầu với paper trading** - Test ít nhất 1-2 tuần
2. **Monitor dashboard** - Xem performance realtime
3. **Check Telegram alerts** - Biết ngay khi có trade
4. **Review logs** - File `logs/trading_YYYY-MM-DD.log` có tất cả trades
5. **Train models thường xuyên** - Mỗi tuần/tháng
6. **Adjust parameters** - Tune trong `.env` dựa trên performance

## 🎯 Mục tiêu Win Rate

- **Good**: >55% win rate
- **Very Good**: >60% win rate
- **Excellent**: >65% win rate

Với scalping (trade nhanh), 55-60% là rất tốt!

## 📞 Support

- **Issues**: https://github.com/your-username/coin_pred/issues
- **Docs**: Xem GUIDE.md
- **Logs**: Check `logs/` directory

---

**Good luck trading! 🚀📈**

Remember:
- Never invest more than you can afford to lose
- This is experimental software
- Crypto trading is risky
- Past performance ≠ Future results

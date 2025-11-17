"""
Enhanced Streamlit Dashboard V2 with professional UI/UX.
- Real-time monitoring
- Advanced charts
- Risk metrics
- Trade analytics
- System controls
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import time

from config import settings
from src.database import db, init_database, TradeRepository, OHLCVRepository
from src.data_collection import binance_client
from src.utils import calculate_sharpe_ratio, calculate_max_drawdown


# Page config
st.set_page_config(
    page_title="Crypto Trading Bot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transition: box-shadow 0.3s;
    }
    h1 {
        color: #1f77b4;
        font-weight: 700;
    }
    h2 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    .profit {
        color: #27ae60;
        font-weight: bold;
    }
    .loss {
        color: #e74c3c;
        font-weight: bold;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .alert-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_db_cached():
    """Initialize database (cached)."""
    init_database()
    return db


def get_trading_status():
    """Check if bot is running."""
    # TODO: Implement actual bot status check
    return {
        'running': True,  # Placeholder
        'mode': settings.trading.trading_mode,
        'uptime': '2h 15m',  # Placeholder
    }


def main():
    """Main dashboard."""
    # Initialize DB
    db = init_db_cached()

    # Header
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("🚀 Crypto Trading Bot Dashboard V2")

    with col2:
        status = get_trading_status()
        if status['running']:
            st.markdown(
                '<div class="alert-box alert-success">✅ Bot Running</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="alert-box alert-danger">❌ Bot Stopped</div>',
                unsafe_allow_html=True
            )

    with col3:
        st.markdown(f"**Mode:** {status['mode'].upper()}")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")

        # Symbol selector
        symbol = st.selectbox(
            "Trading Pair",
            settings.trading.target_symbols,
            index=0
        )

        # Timeframe
        timeframe = st.select_slider(
            "Timeframe",
            options=["1D", "7D", "30D", "90D", "ALL"],
            value="7D"
        )

        days_map = {"1D": 1, "7D": 7, "30D": 30, "90D": 90, "ALL": 365}
        days = days_map[timeframe]

        st.divider()

        # Filters
        st.subheader("📊 Filters")
        show_only_profitable = st.checkbox("Show only profitable trades")
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.0, 0.05)

        st.divider()

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh (10s)")
        if auto_refresh:
            time.sleep(10)
            st.rerun()

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "💰 Trades",
        "📈 Charts",
        "⚠️ Risk Metrics",
        "⚙️ System"
    ])

    with tab1:
        show_overview_v2(symbol, days)

    with tab2:
        show_trades_v2(symbol, days, show_only_profitable, min_confidence)

    with tab3:
        show_charts_v2(symbol)

    with tab4:
        show_risk_metrics_v2(days)

    with tab5:
        show_system_info_v2()


def show_overview_v2(symbol: str, days: int):
    """Enhanced overview with advanced metrics."""
    st.header("📊 Performance Overview")

    with db.session_scope() as session:
        # Get performance summary
        summary = TradeRepository.get_performance_summary(session, days=days)

        # Get trades for additional metrics
        trades = TradeRepository.get_closed_trades(session, symbol=None, days=days)

        # Calculate additional metrics
        if trades:
            returns = [t.profit_loss_percent for t in trades if t.profit_loss_percent]
            returns_series = pd.Series(returns) if returns else pd.Series([0])

            sharpe = calculate_sharpe_ratio(returns_series)

            # Calculate equity curve for max drawdown
            equity = [10000]  # Starting balance
            for trade in sorted(trades, key=lambda x: x.entry_time):
                if trade.net_profit_loss:
                    equity.append(equity[-1] + trade.net_profit_loss)

            max_dd = calculate_max_drawdown(pd.Series(equity))
        else:
            sharpe = 0.0
            max_dd = 0.0

        # KPI Metrics Row 1
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Trades",
                f"{summary['total_trades']}",
                help="Total number of completed trades"
            )

        with col2:
            color = "normal" if summary['win_rate'] >= 0.5 else "inverse"
            st.metric(
                "Win Rate",
                f"{summary['win_rate']:.1%}",
                delta=f"{(summary['win_rate'] - 0.5)*100:+.1f}% vs 50%",
                delta_color=color,
                help="Percentage of profitable trades"
            )

        with col3:
            delta_color = "normal" if summary['total_pnl'] > 0 else "inverse"
            st.metric(
                "Total P/L",
                f"${summary['total_pnl']:,.2f}",
                delta=f"{summary['total_pnl']:+.2f}",
                delta_color=delta_color,
                help="Total profit/loss"
            )

        with col4:
            st.metric(
                "Sharpe Ratio",
                f"{sharpe:.2f}",
                help="Risk-adjusted return (>1.5 is good)"
            )

        with col5:
            st.metric(
                "Max Drawdown",
                f"{max_dd:.1%}",
                help="Maximum portfolio decline"
            )

        # KPI Metrics Row 2
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Winning Trades",
                f"{summary['winning_trades']}",
                help="Number of profitable trades"
            )

        with col2:
            st.metric(
                "Losing Trades",
                f"{summary['losing_trades']}",
                help="Number of losing trades"
            )

        with col3:
            st.metric(
                "Avg Profit",
                f"${summary['avg_pnl']:,.2f}",
                help="Average profit per trade"
            )

        with col4:
            profit_factor = abs(summary['largest_win'] / summary['largest_loss']) if summary['largest_loss'] else 0
            st.metric(
                "Profit Factor",
                f"{profit_factor:.2f}",
                help="Ratio of gross profit to gross loss (>2 is excellent)"
            )

        st.divider()

        # Performance Charts
        col1, col2 = st.columns(2)

        with col1:
            # Win/Loss Pie Chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses'],
                values=[summary['winning_trades'], summary['losing_trades']],
                marker=dict(colors=['#27ae60', '#e74c3c']),
                hole=0.4
            )])
            fig_pie.update_layout(
                title="Win/Loss Distribution",
                height=300,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # P/L Bar Chart
            df_pnl = pd.DataFrame({
                'Type': ['Largest Win', 'Largest Loss', 'Avg P/L'],
                'Amount': [
                    summary['largest_win'],
                    abs(summary['largest_loss']),
                    abs(summary['avg_pnl'])
                ],
                'Color': ['#27ae60', '#e74c3c', '#3498db']
            })

            fig_bar = px.bar(
                df_pnl,
                x='Type',
                y='Amount',
                color='Type',
                color_discrete_map={
                    'Largest Win': '#27ae60',
                    'Largest Loss': '#e74c3c',
                    'Avg P/L': '#3498db'
                }
            )
            fig_bar.update_layout(
                title="P/L Statistics",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Equity Curve
        if len(equity) > 1:
            st.subheader("📈 Equity Curve")

            equity_df = pd.DataFrame({
                'Trade #': range(len(equity)),
                'Equity': equity
            })

            fig_equity = px.line(
                equity_df,
                x='Trade #',
                y='Equity',
                title="Portfolio Equity Over Time"
            )
            fig_equity.add_hline(
                y=10000,
                line_dash="dash",
                line_color="gray",
                annotation_text="Starting Balance"
            )
            fig_equity.update_layout(height=400)
            st.plotly_chart(fig_equity, use_container_width=True)


def show_trades_v2(symbol: str, days: int, only_profitable: bool, min_confidence: float):
    """Enhanced trade history."""
    st.header(f"💰 Trade History - Last {days} Days")

    with db.session_scope() as session:
        trades = TradeRepository.get_closed_trades(session, symbol=None, days=days)

        if not trades:
            st.info(f"No trades found in the last {days} days")
            return

        # Apply filters
        if only_profitable:
            trades = [t for t in trades if t.net_profit_loss and t.net_profit_loss > 0]

        if min_confidence > 0:
            trades = [t for t in trades if t.entry_confidence and t.entry_confidence >= min_confidence]

        if not trades:
            st.warning("No trades match the selected filters")
            return

        # Convert to DataFrame
        trades_data = []
        for trade in trades:
            trades_data.append({
                'ID': trade.id,
                'Symbol': trade.symbol,
                'Side': trade.side.value.upper(),
                'Entry': trade.entry_time.strftime('%Y-%m-%d %H:%M'),
                'Exit': trade.exit_time.strftime('%Y-%m-%d %H:%M') if trade.exit_time else 'N/A',
                'Entry $': trade.entry_price,
                'Exit $': trade.exit_price,
                'Qty': trade.quantity,
                'P/L $': trade.net_profit_loss,
                'P/L %': trade.profit_loss_percent * 100 if trade.profit_loss_percent else 0,
                'Confidence': trade.entry_confidence * 100 if trade.entry_confidence else 0,
                'Duration': str(trade.exit_time - trade.entry_time).split('.')[0] if trade.exit_time else 'N/A'
            })

        df = pd.DataFrame(trades_data)

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Filtered Trades", len(df))
        with col2:
            avg_pnl = df['P/L $'].mean()
            st.metric("Avg P/L", f"${avg_pnl:,.2f}")
        with col3:
            win_rate = len(df[df['P/L $'] > 0]) / len(df) if len(df) > 0 else 0
            st.metric("Win Rate", f"{win_rate:.1%}")
        with col4:
            total_pnl = df['P/L $'].sum()
            st.metric("Total P/L", f"${total_pnl:,.2f}")

        st.divider()

        # Data table with custom styling
        st.dataframe(
            df.style.applymap(
                lambda x: 'color: #27ae60; font-weight: bold' if isinstance(x, (int, float)) and x > 0 and 'P/L' in df.columns.tolist() else
                          'color: #e74c3c; font-weight: bold' if isinstance(x, (int, float)) and x < 0 and 'P/L' in df.columns.tolist() else '',
                subset=['P/L $', 'P/L %']
            ).format({
                'Entry $': '${:,.2f}',
                'Exit $': '${:,.2f}',
                'Qty': '{:.6f}',
                'P/L $': '${:+,.2f}',
                'P/L %': '{:+.2f}%',
                'Confidence': '{:.1f}%'
            }),
            use_container_width=True,
            height=500
        )

        # Trade distribution by symbol
        st.subheader("📊 Trade Distribution")

        col1, col2 = st.columns(2)

        with col1:
            symbol_dist = df['Symbol'].value_counts()
            fig_symbol = px.pie(
                values=symbol_dist.values,
                names=symbol_dist.index,
                title="Trades by Symbol"
            )
            st.plotly_chart(fig_symbol, use_container_width=True)

        with col2:
            side_dist = df['Side'].value_counts()
            fig_side = px.bar(
                x=side_dist.index,
                y=side_dist.values,
                title="Trades by Side",
                color=side_dist.index,
                color_discrete_map={'BUY': '#3498db', 'SELL': '#e67e22'}
            )
            st.plotly_chart(fig_side, use_container_width=True)


def show_charts_v2(symbol: str):
    """Enhanced charts with multiple indicators."""
    st.header(f"📈 Advanced Charts - {symbol}")

    try:
        # Get data
        df = binance_client.get_historical_klines(symbol, "1h", limit=168)

        if df.empty:
            st.error("No data available")
            return

        # Create subplot with 3 rows
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Price', 'Volume', 'RSI')
        )

        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price'
            ),
            row=1,
            col=1
        )

        # Volume bars
        colors = ['#27ae60' if close >= open else '#e74c3c'
                  for close, open in zip(df['close'], df['open'])]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['volume'],
                name='Volume',
                marker_color=colors
            ),
            row=2,
            col=1
        )

        # RSI (calculate simple RSI)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=rsi,
                name='RSI',
                line=dict(color='#3498db')
            ),
            row=3,
            col=1
        )

        # RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        # Update layout
        fig.update_layout(
            title=f"{symbol} - 1H Chart",
            height=800,
            xaxis_rangeslider_visible=False,
            showlegend=False
        )

        fig.update_yaxes(title_text="Price (USDT)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Current price info
        current_price = binance_client.get_price(symbol)
        ticker = binance_client.get_ticker(symbol)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Current Price", f"${current_price:,.2f}")

        with col2:
            change_24h = float(ticker['priceChangePercent'])
            st.metric("24h Change", f"{change_24h:+.2f}%", delta=f"{change_24h:+.2f}%")

        with col3:
            st.metric("24h High", f"${float(ticker['highPrice']):,.2f}")

        with col4:
            st.metric("24h Low", f"${float(ticker['lowPrice']):,.2f}")

    except Exception as e:
        st.error(f"Error loading chart: {e}")


def show_risk_metrics_v2(days: int):
    """Enhanced risk metrics dashboard."""
    st.header("⚠️ Risk Metrics & Analysis")

    with db.session_scope() as session:
        summary = TradeRepository.get_performance_summary(session, days=days)
        open_trades = TradeRepository.get_open_trades(session)

        # Risk Overview
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Open Positions",
                len(open_trades),
                help="Currently open positions"
            )

        with col2:
            max_allowed = settings.trading.max_concurrent_positions
            usage = len(open_trades) / max_allowed if max_allowed > 0 else 0
            st.metric(
                "Position Capacity",
                f"{usage:.0%}",
                delta=f"{len(open_trades)}/{max_allowed}",
                help="Percentage of max concurrent positions used"
            )

        with col3:
            daily_loss = summary['total_pnl'] if summary['total_pnl'] < 0 else 0
            max_loss = settings.trading.max_daily_loss * 10000  # Assuming 10k balance
            loss_usage = abs(daily_loss) / max_loss if max_loss > 0 else 0

            st.metric(
                "Daily Loss Usage",
                f"{loss_usage:.0%}",
                help="Percentage of max daily loss used"
            )

        with col4:
            # Risk score (simplified)
            risk_score = (usage + loss_usage) / 2

            if risk_score < 0.5:
                color = "🟢 Low"
            elif risk_score < 0.75:
                color = "🟡 Medium"
            else:
                color = "🔴 High"

            st.metric(
                "Risk Level",
                color,
                help="Overall risk assessment"
            )

        st.divider()

        # Warnings & Alerts
        st.subheader("⚠️ Active Alerts")

        warnings = []

        if summary['win_rate'] < 0.5:
            warnings.append({
                'level': 'warning',
                'message': f"Win rate below 50% ({summary['win_rate']:.1%})"
            })

        if len(open_trades) >= settings.trading.max_concurrent_positions:
            warnings.append({
                'level': 'danger',
                'message': "Maximum concurrent positions reached"
            })

        if daily_loss < -max_loss * 0.8:
            warnings.append({
                'level': 'danger',
                'message': f"Approaching daily loss limit (${abs(daily_loss):,.2f})"
            })

        if not warnings:
            st.markdown(
                '<div class="alert-box alert-success">✅ No active warnings</div>',
                unsafe_allow_html=True
            )
        else:
            for warning in warnings:
                level_class = f"alert-{warning['level']}"
                icon = "⚠️" if warning['level'] == 'warning' else "🚨"
                st.markdown(
                    f'<div class="alert-box {level_class}">{icon} {warning["message"]}</div>',
                    unsafe_allow_html=True
                )


def show_system_info_v2():
    """Enhanced system information."""
    st.header("⚙️ System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Configuration")

        config_data = {
            'Trading Mode': settings.trading.trading_mode.upper(),
            'Target Symbols': ', '.join(settings.trading.target_symbols),
            'Max Position Size': f"{settings.trading.max_position_size * 100}%",
            'Stop Loss': f"{settings.trading.stop_loss_percent * 100}%",
            'Take Profit': f"{settings.trading.take_profit_percent * 100}%",
            'Min Confidence': f"{settings.trading.min_confidence_score * 100}%",
            'Max Concurrent Positions': settings.trading.max_concurrent_positions,
            'Max Daily Loss': f"{settings.trading.max_daily_loss * 100}%"
        }

        df_config = pd.DataFrame(list(config_data.items()), columns=['Setting', 'Value'])
        st.table(df_config)

    with col2:
        st.subheader("🗄️ Database Status")

        try:
            db_stats = {
                'OHLCV Records': db.get_table_count('ohlcv'),
                'Total Trades': db.get_table_count('trades'),
                'Predictions': db.get_table_count('predictions'),
                'Features': db.get_table_count('features'),
                'Sentiment Data': db.get_table_count('sentiment_data')
            }

            df_db = pd.DataFrame(list(db_stats.items()), columns=['Table', 'Rows'])
            st.table(df_db)

            if db.check_connection():
                st.success("✅ Database Connected")
            else:
                st.error("❌ Database Connection Failed")

        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # API Status
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌐 Binance API Status")
        try:
            if binance_client.ping():
                st.success("✅ Connected")
                server_time = binance_client.get_server_time()
                st.write(f"Server Time: {server_time}")
            else:
                st.error("❌ Connection Failed")
        except Exception as e:
            st.error(f"Error: {e}")

    with col2:
        st.subheader("📱 Telegram Status")
        from src.utils import telegram

        if telegram.enabled:
            st.success("✅ Enabled")
            st.write(f"Chat ID: {telegram.chat_id[:10]}...")
        else:
            st.warning("⚠️ Disabled")


if __name__ == "__main__":
    main()

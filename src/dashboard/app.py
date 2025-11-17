"""
Streamlit dashboard for monitoring trading bot performance.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from config import settings
from src.database import db, init_database, TradeRepository, OHLCVRepository, PerformanceRepository
from src.data_collection import binance_client


# Page config
st.set_page_config(
    page_title="Crypto Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def init_db():
    """Initialize database."""
    init_database()
    return db


def main():
    """Main dashboard."""
    st.title("📈 Crypto Trading Bot Dashboard")

    # Initialize DB
    db = init_db()

    # Sidebar
    st.sidebar.header("⚙️ Settings")

    # Select symbol
    symbol = st.sidebar.selectbox(
        "Select Symbol",
        settings.trading.target_symbols
    )

    # Select timeframe
    days = st.sidebar.slider("Days to show", 1, 30, 7)

    # Refresh button
    if st.sidebar.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Trades", "📉 Chart", "⚙️ System"])

    with tab1:
        show_overview(symbol, days)

    with tab2:
        show_trades(symbol, days)

    with tab3:
        show_chart(symbol)

    with tab4:
        show_system_info()


def show_overview(symbol: str, days: int):
    """Show overview metrics."""
    st.header("Performance Overview")

    with db.session_scope() as session:
        # Get performance summary
        summary = TradeRepository.get_performance_summary(session, days=days)

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Trades",
                summary['total_trades'],
                help="Total number of trades executed"
            )

        with col2:
            st.metric(
                "Win Rate",
                f"{summary['win_rate']:.1%}",
                help="Percentage of profitable trades"
            )

        with col3:
            st.metric(
                "Total P/L",
                f"${summary['total_pnl']:,.2f}",
                delta=f"{summary['total_pnl']:+.2f}",
                help="Total profit/loss"
            )

        with col4:
            st.metric(
                "Avg P/L",
                f"${summary['avg_pnl']:,.2f}",
                help="Average profit/loss per trade"
            )

        # Win/Loss breakdown
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Win/Loss Breakdown")
            fig = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses'],
                values=[summary['winning_trades'], summary['losing_trades']],
                marker=dict(colors=['#00cc00', '#cc0000'])
            )])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("P/L Distribution")
            if summary['largest_win'] or summary['largest_loss']:
                df_pnl = pd.DataFrame({
                    'Type': ['Largest Win', 'Largest Loss'],
                    'Amount': [summary['largest_win'], abs(summary['largest_loss'])]
                })
                fig = px.bar(df_pnl, x='Type', y='Amount', color='Type',
                            color_discrete_map={'Largest Win': '#00cc00', 'Largest Loss': '#cc0000'})
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)


def show_trades(symbol: str, days: int):
    """Show trade history."""
    st.header(f"Trade History - {symbol}")

    with db.session_scope() as session:
        # Get trades
        trades = TradeRepository.get_closed_trades(session, symbol=symbol, days=days)

        if not trades:
            st.info(f"No trades found for {symbol} in the last {days} days")
            return

        # Convert to DataFrame
        trades_data = []
        for trade in trades:
            trades_data.append({
                'ID': trade.id,
                'Side': trade.side.value.upper(),
                'Entry Time': trade.entry_time,
                'Exit Time': trade.exit_time,
                'Entry Price': trade.entry_price,
                'Exit Price': trade.exit_price,
                'Quantity': trade.quantity,
                'P/L': trade.net_profit_loss,
                'P/L %': trade.profit_loss_percent * 100,
                'Status': trade.status.value
            })

        df = pd.DataFrame(trades_data)

        # Color code P/L
        def highlight_pnl(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'background-color: #d4edda'
                elif val < 0:
                    return 'background-color: #f8d7da'
            return ''

        st.dataframe(
            df.style.applymap(highlight_pnl, subset=['P/L', 'P/L %']),
            use_container_width=True,
            height=400
        )

        # Show recent trades details
        st.subheader("Recent Trades")
        for trade in trades[:5]:
            with st.expander(f"Trade #{trade.id} - {trade.side.value.upper()} - {trade.entry_time.strftime('%Y-%m-%d %H:%M')}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Entry:**")
                    st.write(f"Price: ${trade.entry_price:,.2f}")
                    st.write(f"Time: {trade.entry_time.strftime('%Y-%m-%d %H:%M')}")

                with col2:
                    st.write("**Exit:**")
                    st.write(f"Price: ${trade.exit_price:,.2f}")
                    st.write(f"Time: {trade.exit_time.strftime('%Y-%m-%d %H:%M')}")

                with col3:
                    st.write("**Result:**")
                    pnl_color = "green" if trade.net_profit_loss > 0 else "red"
                    st.write(f"P/L: :{pnl_color}[${trade.net_profit_loss:+,.2f}]")
                    st.write(f"P/L %: :{pnl_color}[{trade.profit_loss_percent:+.2%}]")

                if trade.notes:
                    st.write(f"**Notes:** {trade.notes}")


def show_chart(symbol: str):
    """Show price chart."""
    st.header(f"Price Chart - {symbol}")

    try:
        # Get recent data
        df = binance_client.get_historical_klines(symbol, "1h", limit=168)  # 1 week

        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol
        )])

        fig.update_layout(
            title=f"{symbol} - 1H Candlestick Chart",
            yaxis_title="Price (USDT)",
            xaxis_title="Time",
            height=600,
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Show current price
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


def show_system_info():
    """Show system information."""
    st.header("System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")
        st.write(f"**Trading Mode:** {settings.trading.trading_mode.upper()}")
        st.write(f"**Target Symbols:** {', '.join(settings.trading.target_symbols)}")
        st.write(f"**Max Position Size:** {settings.trading.max_position_size * 100}%")
        st.write(f"**Stop Loss:** {settings.trading.stop_loss_percent * 100}%")
        st.write(f"**Take Profit:** {settings.trading.take_profit_percent * 100}%")
        st.write(f"**Min Confidence:** {settings.trading.min_confidence_score * 100}%")

    with col2:
        st.subheader("Database Status")
        try:
            with db.session_scope() as session:
                ohlcv_count = db.get_table_count('ohlcv')
                trades_count = db.get_table_count('trades')
                predictions_count = db.get_table_count('predictions')

                st.write(f"**OHLCV Records:** {ohlcv_count:,}")
                st.write(f"**Total Trades:** {trades_count:,}")
                st.write(f"**Predictions:** {predictions_count:,}")

                if db.check_connection():
                    st.success("✅ Database Connected")
                else:
                    st.error("❌ Database Connection Failed")
        except Exception as e:
            st.error(f"Error: {e}")

    # Binance API Status
    st.subheader("Binance API Status")
    try:
        if binance_client.ping():
            st.success("✅ Binance API Connected")
            server_time = binance_client.get_server_time()
            st.write(f"**Server Time:** {server_time}")
        else:
            st.error("❌ Binance API Connection Failed")
    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    main()

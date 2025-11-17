"""Main application window."""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QAction, QMessageBox,
    QDialog, QFormLayout, QPushButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime, timedelta
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from src.database import db, init_database
from src.gui.widgets import (
    PriceWidget, TradingPanel, MonitoringWidget,
    HistoryWidget, ChartWidget
)
from src.gui.workers import (
    PriceUpdateWorker, TradeHistoryWorker, PerformanceWorker,
    ChartDataWorker, OpenPositionsWorker, SystemStatsWorker
)
from src.utils import log


class MainWindow(QMainWindow):
    """Main application window with tabs."""

    def __init__(self):
        super().__init__()
        self.workers = []
        self.bot_start_time = None
        self.init_ui()
        self.init_database()
        self.start_background_workers()

    def init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Crypto Trading Bot - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background: white;
            }
            QTabBar::tab {
                background: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #007bff;
                color: white;
            }
            QTabBar::tab:hover {
                background: #0056b3;
                color: white;
            }
        """)

        # Create tabs
        self.price_widget = PriceWidget()
        self.trading_panel = TradingPanel()
        self.monitoring_widget = MonitoringWidget()
        self.history_widget = HistoryWidget()
        self.chart_widget = ChartWidget()

        # Add tabs
        self.tabs.addTab(self._create_dashboard_tab(), "📊 Dashboard")
        self.tabs.addTab(self.trading_panel, "🤖 Trading Control")
        self.tabs.addTab(self.monitoring_widget, "📈 Live Monitoring")
        self.tabs.addTab(self.history_widget, "📜 Trade History")
        self.tabs.addTab(self.chart_widget, "📉 Charts")

        main_layout.addWidget(self.tabs)

        central_widget.setLayout(main_layout)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Menu bar
        self._create_menu_bar()

        # Connect signals
        self._connect_signals()

        # Uptime timer
        self.uptime_timer = QTimer()
        self.uptime_timer.timeout.connect(self._update_uptime)

    def _create_header(self):
        """Create application header."""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout()

        # Title
        title = QLabel("🚀 Crypto Trading Bot")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        layout.addStretch()

        # System time
        self.time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.time_label.setFont(QFont("Arial", 10))
        self.time_label.setStyleSheet("color: white;")
        layout.addWidget(self.time_label)

        # Update time every second
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)

        header_widget.setLayout(layout)
        return header_widget

    def _create_dashboard_tab(self):
        """Create main dashboard tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Welcome message
        welcome = QLabel("Welcome to Crypto Trading Bot")
        welcome.setFont(QFont("Arial", 16, QFont.Bold))
        welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome)

        # Price widget
        layout.addWidget(self.price_widget)

        # Quick stats (will be added later)

        widget.setLayout(layout)
        return widget

    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        refresh_action = QAction("&Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._on_refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        """Connect widget signals."""
        # Trading panel signals
        self.trading_panel.start_bot_signal.connect(self._on_bot_start)
        self.trading_panel.stop_bot_signal.connect(self._on_bot_stop)
        self.trading_panel.manual_trade_signal.connect(self._on_manual_trade)

        # Chart refresh
        self.chart_widget.findChild(QPushButton).clicked.connect(self._load_chart_data)

    def init_database(self):
        """Initialize database."""
        try:
            init_database()
            self.statusBar.showMessage("✅ Database initialized", 3000)
            log.info("Database initialized successfully")
        except Exception as e:
            self.statusBar.showMessage(f"⚠️ Database error: {str(e)}", 5000)
            log.error(f"Database initialization failed: {e}")

    def start_background_workers(self):
        """Start all background workers."""
        # Price update worker
        self.price_worker = PriceUpdateWorker(settings.trading.target_symbols, interval=2)
        self.price_worker.price_updated.connect(self.price_widget.update_prices)
        self.price_worker.error_occurred.connect(self._on_worker_error)
        self.price_worker.start()
        self.workers.append(self.price_worker)

        # Open positions worker
        self.positions_worker = OpenPositionsWorker(interval=5)
        self.positions_worker.positions_updated.connect(self.monitoring_widget.update_positions)
        self.positions_worker.error_occurred.connect(self._on_worker_error)
        self.positions_worker.start()
        self.workers.append(self.positions_worker)

        # Performance worker
        self.performance_worker = PerformanceWorker(days=30)
        self.performance_worker.metrics_loaded.connect(self.monitoring_widget.update_metrics)
        self.performance_worker.error_occurred.connect(self._on_worker_error)
        self.performance_worker.start()
        self.workers.append(self.performance_worker)

        # System stats worker
        self.stats_worker = SystemStatsWorker(interval=10)
        self.stats_worker.stats_updated.connect(self._on_stats_updated)
        self.stats_worker.error_occurred.connect(self._on_worker_error)
        self.stats_worker.start()
        self.workers.append(self.stats_worker)

        log.info("All background workers started")

    def _on_bot_start(self, mode: str):
        """Handle bot start."""
        log.info(f"Bot started in {mode} mode")
        self.bot_start_time = datetime.now()
        self.uptime_timer.start(1000)  # Update every second
        self.statusBar.showMessage(f"🟢 Bot running in {mode.upper()} mode")

    def _on_bot_stop(self):
        """Handle bot stop."""
        log.info("Bot stopped")
        self.bot_start_time = None
        self.uptime_timer.stop()
        self.statusBar.showMessage("⚫ Bot stopped")

    def _on_manual_trade(self, params: dict):
        """Handle manual trade."""
        log.info(f"Manual trade: {params}")
        QMessageBox.information(
            self,
            "Manual Trade",
            f"Manual trade executed:\n{params}"
        )

    def _on_worker_error(self, error: str):
        """Handle worker errors."""
        log.error(f"Worker error: {error}")
        self.statusBar.showMessage(f"⚠️ Error: {error}", 5000)

    def _on_stats_updated(self, stats: dict):
        """Handle system stats update."""
        # Update status bar with database info
        total_records = stats.get('ohlcv_records', 0)
        self.statusBar.showMessage(
            f"Database: {total_records:,} OHLCV records | "
            f"{stats.get('total_trades', 0)} trades"
        )

    def _update_time(self):
        """Update system time display."""
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def _update_uptime(self):
        """Update bot uptime."""
        if self.bot_start_time:
            uptime = datetime.now() - self.bot_start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.trading_panel.update_uptime(uptime_str)

    def _load_chart_data(self):
        """Load chart data for selected symbol and timeframe."""
        symbol = self.chart_widget.get_selected_symbol()
        timeframe = self.chart_widget.get_selected_timeframe()

        # Create worker to load data
        worker = ChartDataWorker(symbol, timeframe, limit=100)
        worker.data_loaded.connect(self.chart_widget.update_chart)
        worker.error_occurred.connect(self._on_worker_error)
        worker.start()

    def _on_refresh_all(self):
        """Refresh all data."""
        self.statusBar.showMessage("🔄 Refreshing all data...", 2000)

        # Reload trade history
        worker = TradeHistoryWorker(days=30)
        worker.trades_loaded.connect(self.history_widget.update_trades)
        worker.error_occurred.connect(self._on_worker_error)
        worker.start()

        # Reload performance
        perf_worker = PerformanceWorker(days=30)
        perf_worker.metrics_loaded.connect(self.monitoring_widget.update_metrics)
        perf_worker.error_occurred.connect(self._on_worker_error)
        perf_worker.start()

        log.info("Refreshing all data")

    def _show_settings(self):
        """Show settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        layout.addRow(QLabel("Settings panel coming soon..."))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addRow("", close_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Crypto Trading Bot",
            "<h2>Crypto Trading Bot v2.0</h2>"
            "<p>Professional cryptocurrency trading bot with:</p>"
            "<ul>"
            "<li>Real-time price monitoring</li>"
            "<li>Machine learning predictions</li>"
            "<li>Advanced risk management</li>"
            "<li>Automated trading execution</li>"
            "</ul>"
            "<p><b>Built with PyQt5 and Python</b></p>"
            "<p>© 2025 - All rights reserved</p>"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop all workers
        for worker in self.workers:
            if hasattr(worker, 'stop'):
                worker.stop()
            else:
                worker.quit()
                worker.wait()

        log.info("Application closed")
        event.accept()

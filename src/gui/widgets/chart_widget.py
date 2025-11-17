"""Real-time chart widget using pyqtgraph."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from datetime import datetime
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings


class ChartWidget(QWidget):
    """Real-time candlestick chart with volume."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title and controls
        header_layout = QHBoxLayout()

        title = QLabel("📊 Price Chart")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Symbol selector
        header_layout.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(settings.trading.target_symbols)
        header_layout.addWidget(self.symbol_combo)

        # Timeframe selector
        header_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "1h", "4h", "1d"])
        self.timeframe_combo.setCurrentText("1h")
        header_layout.addWidget(self.timeframe_combo)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Create pyqtgraph chart widget
        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_widget.setBackground('w')

        # Price plot (candlestick)
        self.price_plot = self.graphics_widget.addPlot(row=0, col=0, title="Price")
        self.price_plot.showGrid(x=True, y=True, alpha=0.3)
        self.price_plot.setLabel('left', 'Price', units='$')

        # Candlestick items
        self.candlestick_item = pg.CandlestickItem()
        self.price_plot.addItem(self.candlestick_item)

        # Volume plot
        self.graphics_widget.nextRow()
        self.volume_plot = self.graphics_widget.addPlot(row=1, col=0, title="Volume")
        self.volume_plot.showGrid(x=True, y=True, alpha=0.3)
        self.volume_plot.setLabel('left', 'Volume')
        self.volume_plot.setMaximumHeight(150)

        # Volume bars
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.6, brush='b')
        self.volume_plot.addItem(self.volume_bars)

        # Link x-axes
        self.volume_plot.setXLink(self.price_plot)

        layout.addWidget(self.graphics_widget)

        # Status label
        self.status_label = QLabel("Select symbol and click Refresh to load chart")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    @pyqtSlot(object)
    def update_chart(self, df):
        """
        Update chart with new data.

        Args:
            df: Pandas DataFrame with OHLCV data
        """
        try:
            if df is None or df.empty:
                self.status_label.setText("⚠️ No data available")
                self.status_label.setStyleSheet("color: #ffc107;")
                return

            self.current_data = df

            # Prepare candlestick data
            # pyqtgraph expects: time, open, close, min, max
            times = np.arange(len(df))

            candlestick_data = []
            for i, (timestamp, row) in enumerate(df.iterrows()):
                candlestick_data.append({
                    'time': i,
                    'open': row['open'],
                    'close': row['close'],
                    'min': row['low'],
                    'max': row['high']
                })

            # Update candlestick
            self.candlestick_item.setData(candlestick_data)

            # Update volume bars
            volumes = df['volume'].values
            volume_colors = []
            for i, (timestamp, row) in enumerate(df.iterrows()):
                # Green if close > open, red otherwise
                if row['close'] >= row['open']:
                    volume_colors.append((0, 255, 0, 150))  # Green
                else:
                    volume_colors.append((255, 0, 0, 150))  # Red

            self.volume_bars.setOpts(
                x=times,
                height=volumes,
                width=0.6,
                brushes=volume_colors
            )

            # Update status
            symbol = self.symbol_combo.currentText()
            timeframe = self.timeframe_combo.currentText()
            self.status_label.setText(
                f"✅ Showing {len(df)} candles for {symbol} ({timeframe})"
            )
            self.status_label.setStyleSheet("color: #28a745; font-style: italic;")

            # Auto-range
            self.price_plot.enableAutoRange()
            self.volume_plot.enableAutoRange()

        except Exception as e:
            self.status_label.setText(f"⚠️ Chart error: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545; font-style: italic;")

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        # Signal parent to reload chart data
        self.status_label.setText("🔄 Loading chart data...")
        self.status_label.setStyleSheet("color: #007bff; font-style: italic;")

    def get_selected_symbol(self):
        """Get currently selected symbol."""
        return self.symbol_combo.currentText()

    def get_selected_timeframe(self):
        """Get currently selected timeframe."""
        return self.timeframe_combo.currentText()

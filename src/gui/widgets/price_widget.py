"""Real-time price display widget."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QFont
from typing import Dict


class PriceWidget(QWidget):
    """Real-time cryptocurrency prices display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.price_cache = {}

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("📊 Real-Time Prices")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Price table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Symbol", "Price", "24h Change %", "24h High", "24h Low", "Volume"
        ])

        # Table styling
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #f8f9fa;
                alternate-background-color: #e9ecef;
                gridline-color: #dee2e6;
                font-size: 11pt;
            }
            QHeaderView::section {
                background-color: #343a40;
                color: white;
                padding: 8px;
                font-weight: bold;
                font-size: 10pt;
            }
        """)

        # Auto-resize columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)

        # Status label
        self.status_label = QLabel("Waiting for data...")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    @pyqtSlot(dict)
    def update_prices(self, prices: Dict):
        """
        Update price display.

        Args:
            prices: Dict of {symbol: {price, change_24h, volume_24h, ...}}
        """
        try:
            # Update row count
            self.table.setRowCount(len(prices))

            row = 0
            for symbol, data in prices.items():
                if data is None:
                    continue

                # Check if price changed (for animation)
                old_price = self.price_cache.get(symbol, {}).get('price', 0)
                new_price = data['price']
                price_changed_up = new_price > old_price
                price_changed_down = new_price < old_price

                # Symbol
                symbol_item = QTableWidgetItem(symbol)
                symbol_item.setFont(QFont("Arial", 11, QFont.Bold))
                self.table.setItem(row, 0, symbol_item)

                # Price
                price_item = QTableWidgetItem(f"${new_price:,.2f}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                price_font = QFont("Arial", 12, QFont.Bold)
                price_item.setFont(price_font)

                # Color based on change
                if price_changed_up:
                    price_item.setForeground(QColor("#27ae60"))  # Green
                elif price_changed_down:
                    price_item.setForeground(QColor("#e74c3c"))  # Red

                self.table.setItem(row, 1, price_item)

                # 24h Change %
                change_24h = data.get('change_24h', 0)
                change_item = QTableWidgetItem(f"{change_24h:+.2f}%")
                change_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                if change_24h > 0:
                    change_item.setForeground(QColor("#27ae60"))  # Green
                    change_item.setBackground(QColor("#d4edda"))  # Light green bg
                elif change_24h < 0:
                    change_item.setForeground(QColor("#e74c3c"))  # Red
                    change_item.setBackground(QColor("#f8d7da"))  # Light red bg

                change_font = QFont("Arial", 10, QFont.Bold)
                change_item.setFont(change_font)
                self.table.setItem(row, 2, change_item)

                # 24h High
                high_item = QTableWidgetItem(f"${data.get('high_24h', 0):,.2f}")
                high_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 3, high_item)

                # 24h Low
                low_item = QTableWidgetItem(f"${data.get('low_24h', 0):,.2f}")
                low_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 4, low_item)

                # Volume
                volume = data.get('volume_24h', 0)
                if volume >= 1_000_000:
                    volume_str = f"${volume/1_000_000:.1f}M"
                elif volume >= 1_000:
                    volume_str = f"${volume/1_000:.1f}K"
                else:
                    volume_str = f"${volume:.2f}"

                volume_item = QTableWidgetItem(volume_str)
                volume_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 5, volume_item)

                row += 1

            # Cache prices for next update
            self.price_cache = prices

            # Update status
            self.status_label.setText(f"✅ Last updated: {self._get_current_time()}")
            self.status_label.setStyleSheet("color: #28a745; font-style: italic;")

        except Exception as e:
            self.status_label.setText(f"⚠️ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545; font-style: italic;")

    def _get_current_time(self):
        """Get current time string."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

"""Real-time monitoring widget for open positions and metrics."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QFont
from typing import List, Dict


class MonitoringWidget(QWidget):
    """Real-time monitoring of open positions and performance."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("📈 Live Monitoring")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Performance metrics group
        metrics_group = self._create_metrics_group()
        layout.addWidget(metrics_group)

        # Open positions table
        positions_label = QLabel("📊 Open Positions")
        positions_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(positions_label)

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(9)
        self.positions_table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Side", "Entry Price", "Current Price",
            "Quantity", "Unrealized P/L", "P/L %", "Entry Time"
        ])

        # Table styling
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.setStyleSheet("""
            QTableWidget {
                background-color: #f8f9fa;
                alternate-background-color: #e9ecef;
                gridline-color: #dee2e6;
                font-size: 10pt;
            }
            QHeaderView::section {
                background-color: #343a40;
                color: white;
                padding: 8px;
                font-weight: bold;
                font-size: 9pt;
            }
        """)

        # Auto-resize columns
        header = self.positions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        layout.addWidget(self.positions_table)

        # Status label
        self.status_label = QLabel("Waiting for data...")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _create_metrics_group(self):
        """Create performance metrics group."""
        group = QGroupBox("Performance Metrics")
        layout = QHBoxLayout()

        # Total P/L
        self.total_pnl_label = self._create_metric_label("Total P/L", "$0.00", "#6c757d")
        layout.addWidget(self.total_pnl_label)

        # Win Rate
        self.win_rate_label = self._create_metric_label("Win Rate", "0%", "#6c757d")
        layout.addWidget(self.win_rate_label)

        # Total Trades
        self.total_trades_label = self._create_metric_label("Total Trades", "0", "#6c757d")
        layout.addWidget(self.total_trades_label)

        # Open Positions
        self.open_positions_label = self._create_metric_label("Open Positions", "0", "#6c757d")
        layout.addWidget(self.open_positions_label)

        group.setLayout(layout)
        return group

    def _create_metric_label(self, title: str, value: str, color: str):
        """Create a metric label widget."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #6c757d; font-size: 9pt;")
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setObjectName(f"{title.replace(' ', '_')}_value")
        layout.addWidget(value_label)

        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """)

        return widget

    @pyqtSlot(list)
    def update_positions(self, positions: List[Dict]):
        """
        Update open positions display.

        Args:
            positions: List of position dicts
        """
        try:
            self.positions_table.setRowCount(len(positions))

            for row, pos in enumerate(positions):
                # ID
                id_item = QTableWidgetItem(str(pos['id']))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.positions_table.setItem(row, 0, id_item)

                # Symbol
                symbol_item = QTableWidgetItem(pos['symbol'])
                symbol_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.positions_table.setItem(row, 1, symbol_item)

                # Side
                side_item = QTableWidgetItem(pos['side'])
                side_item.setTextAlignment(Qt.AlignCenter)
                if pos['side'] == 'BUY':
                    side_item.setForeground(QColor("#28a745"))
                    side_item.setBackground(QColor("#d4edda"))
                else:
                    side_item.setForeground(QColor("#dc3545"))
                    side_item.setBackground(QColor("#f8d7da"))
                side_item.setFont(QFont("Arial", 9, QFont.Bold))
                self.positions_table.setItem(row, 2, side_item)

                # Entry Price
                entry_item = QTableWidgetItem(f"${pos['entry_price']:,.2f}")
                entry_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.positions_table.setItem(row, 3, entry_item)

                # Current Price
                current_item = QTableWidgetItem(f"${pos['current_price']:,.2f}")
                current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                current_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.positions_table.setItem(row, 4, current_item)

                # Quantity
                qty_item = QTableWidgetItem(f"{pos['quantity']:.6f}")
                qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.positions_table.setItem(row, 5, qty_item)

                # Unrealized P/L
                pnl = pos['unrealized_pnl']
                pnl_item = QTableWidgetItem(f"${pnl:,.2f}")
                pnl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                pnl_item.setFont(QFont("Arial", 10, QFont.Bold))

                if pnl > 0:
                    pnl_item.setForeground(QColor("#27ae60"))
                elif pnl < 0:
                    pnl_item.setForeground(QColor("#e74c3c"))

                self.positions_table.setItem(row, 6, pnl_item)

                # P/L %
                pnl_pct = pos['unrealized_pnl_percent']
                pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
                pnl_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                pnl_pct_item.setFont(QFont("Arial", 10, QFont.Bold))

                if pnl_pct > 0:
                    pnl_pct_item.setForeground(QColor("#27ae60"))
                    pnl_pct_item.setBackground(QColor("#d4edda"))
                elif pnl_pct < 0:
                    pnl_pct_item.setForeground(QColor("#e74c3c"))
                    pnl_pct_item.setBackground(QColor("#f8d7da"))

                self.positions_table.setItem(row, 7, pnl_pct_item)

                # Entry Time
                entry_time = pos['entry_time'].strftime("%Y-%m-%d %H:%M:%S") if pos['entry_time'] else "N/A"
                time_item = QTableWidgetItem(entry_time)
                time_item.setTextAlignment(Qt.AlignCenter)
                self.positions_table.setItem(row, 8, time_item)

            # Update status
            self.status_label.setText(f"✅ Monitoring {len(positions)} open position(s)")
            self.status_label.setStyleSheet("color: #28a745; font-style: italic;")

            # Update open positions metric
            self._update_metric_value("Open_Positions_value", str(len(positions)), "#007bff")

        except Exception as e:
            self.status_label.setText(f"⚠️ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545; font-style: italic;")

    @pyqtSlot(dict)
    def update_metrics(self, metrics: Dict):
        """
        Update performance metrics.

        Args:
            metrics: Dict with performance data
        """
        try:
            # Total P/L
            total_pnl = metrics.get('total_pnl', 0)
            pnl_color = "#27ae60" if total_pnl > 0 else "#e74c3c" if total_pnl < 0 else "#6c757d"
            self._update_metric_value("Total_P/L_value", f"${total_pnl:,.2f}", pnl_color)

            # Win Rate
            win_rate = metrics.get('win_rate', 0)
            wr_color = "#27ae60" if win_rate >= 0.6 else "#ffc107" if win_rate >= 0.5 else "#e74c3c"
            self._update_metric_value("Win_Rate_value", f"{win_rate:.1%}", wr_color)

            # Total Trades
            total_trades = metrics.get('total_trades', 0)
            self._update_metric_value("Total_Trades_value", str(total_trades), "#007bff")

        except Exception as e:
            self.status_label.setText(f"⚠️ Metrics error: {str(e)}")

    def _update_metric_value(self, name: str, value: str, color: str):
        """Update a metric value label."""
        # Find the label by object name
        for widget in self.findChildren(QWidget):
            if widget.objectName() == name:
                label = widget.findChildren(QLabel)[0]
                label.setText(value)
                label.setStyleSheet(f"color: {color};")
                break

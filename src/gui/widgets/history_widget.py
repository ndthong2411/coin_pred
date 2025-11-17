"""Trade history viewer widget."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSpinBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QFont
from typing import List, Dict
import csv
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings


class HistoryWidget(QWidget):
    """Trade history viewer with filtering and export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_trades = []
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("📜 Trade History")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Filters
        filter_layout = self._create_filter_layout()
        layout.addLayout(filter_layout)

        # Trade table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Side", "Entry Price", "Exit Price",
            "Quantity", "P/L $", "P/L %", "Confidence", "Entry Time", "Exit Time"
        ])

        # Table styling
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
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
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        # Summary and export
        bottom_layout = QHBoxLayout()

        self.summary_label = QLabel("No trades loaded")
        self.summary_label.setStyleSheet("color: #6c757d; font-style: italic;")
        bottom_layout.addWidget(self.summary_label)

        bottom_layout.addStretch()

        export_btn = QPushButton("📥 Export CSV")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        export_btn.clicked.connect(self._on_export_clicked)
        bottom_layout.addWidget(export_btn)

        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def _create_filter_layout(self):
        """Create filter controls layout."""
        layout = QHBoxLayout()

        # Symbol filter
        layout.addWidget(QLabel("Symbol:"))
        self.symbol_filter = QComboBox()
        self.symbol_filter.addItem("All")
        self.symbol_filter.addItems(settings.trading.target_symbols)
        layout.addWidget(self.symbol_filter)

        # Days filter
        layout.addWidget(QLabel("Days:"))
        self.days_spin = QSpinBox()
        self.days_spin.setMinimum(1)
        self.days_spin.setMaximum(365)
        self.days_spin.setValue(30)
        layout.addWidget(self.days_spin)

        # Profitability filter
        layout.addWidget(QLabel("Filter:"))
        self.profit_filter = QComboBox()
        self.profit_filter.addItems(["All", "Profitable Only", "Losses Only"])
        self.profit_filter.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.profit_filter)

        layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        layout.addWidget(refresh_btn)

        return layout

    @pyqtSlot(list)
    def update_trades(self, trades: List[Dict]):
        """
        Update trade history display.

        Args:
            trades: List of trade dicts
        """
        try:
            self.current_trades = trades
            self._apply_filters()

        except Exception as e:
            self.summary_label.setText(f"⚠️ Error: {str(e)}")
            self.summary_label.setStyleSheet("color: #dc3545; font-style: italic;")

    def _apply_filters(self):
        """Apply filters to trade list."""
        filtered_trades = self.current_trades

        # Apply profitability filter
        profit_filter = self.profit_filter.currentText()
        if profit_filter == "Profitable Only":
            filtered_trades = [t for t in filtered_trades if t.get('profit_loss', 0) > 0]
        elif profit_filter == "Losses Only":
            filtered_trades = [t for t in filtered_trades if t.get('profit_loss', 0) < 0]

        # Display filtered trades
        self._display_trades(filtered_trades)

    def _display_trades(self, trades: List[Dict]):
        """Display trades in table."""
        self.table.setRowCount(len(trades))

        total_pnl = 0
        winning_trades = 0

        for row, trade in enumerate(trades):
            # ID
            id_item = QTableWidgetItem(str(trade['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Symbol
            symbol_item = QTableWidgetItem(trade['symbol'])
            symbol_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.table.setItem(row, 1, symbol_item)

            # Side
            side_item = QTableWidgetItem(trade['side'])
            side_item.setTextAlignment(Qt.AlignCenter)
            if trade['side'] == 'BUY':
                side_item.setForeground(QColor("#28a745"))
                side_item.setBackground(QColor("#d4edda"))
            else:
                side_item.setForeground(QColor("#dc3545"))
                side_item.setBackground(QColor("#f8d7da"))
            side_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.table.setItem(row, 2, side_item)

            # Entry Price
            entry_item = QTableWidgetItem(f"${trade['entry_price']:,.2f}")
            entry_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, entry_item)

            # Exit Price
            exit_price = trade.get('exit_price', 0)
            exit_item = QTableWidgetItem(f"${exit_price:,.2f}" if exit_price else "N/A")
            exit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, exit_item)

            # Quantity
            qty_item = QTableWidgetItem(f"{trade['quantity']:.6f}")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, qty_item)

            # P/L $
            pnl = trade.get('profit_loss', 0) or 0
            pnl_item = QTableWidgetItem(f"${pnl:,.2f}")
            pnl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pnl_item.setFont(QFont("Arial", 10, QFont.Bold))

            if pnl > 0:
                pnl_item.setForeground(QColor("#27ae60"))
                winning_trades += 1
            elif pnl < 0:
                pnl_item.setForeground(QColor("#e74c3c"))

            self.table.setItem(row, 6, pnl_item)
            total_pnl += pnl

            # P/L %
            pnl_pct = trade.get('profit_loss_percent', 0) or 0
            pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
            pnl_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pnl_pct_item.setFont(QFont("Arial", 10, QFont.Bold))

            if pnl_pct > 0:
                pnl_pct_item.setForeground(QColor("#27ae60"))
                pnl_pct_item.setBackground(QColor("#d4edda"))
            elif pnl_pct < 0:
                pnl_pct_item.setForeground(QColor("#e74c3c"))
                pnl_pct_item.setBackground(QColor("#f8d7da"))

            self.table.setItem(row, 7, pnl_pct_item)

            # Confidence
            confidence = trade.get('confidence', 0) or 0
            conf_item = QTableWidgetItem(f"{confidence:.1%}")
            conf_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 8, conf_item)

            # Entry Time
            entry_time = trade['entry_time'].strftime("%Y-%m-%d %H:%M:%S") if trade.get('entry_time') else "N/A"
            entry_time_item = QTableWidgetItem(entry_time)
            entry_time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 9, entry_time_item)

            # Exit Time
            exit_time = trade['exit_time'].strftime("%Y-%m-%d %H:%M:%S") if trade.get('exit_time') else "N/A"
            exit_time_item = QTableWidgetItem(exit_time)
            exit_time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 10, exit_time_item)

        # Update summary
        win_rate = (winning_trades / len(trades) * 100) if len(trades) > 0 else 0
        self.summary_label.setText(
            f"✅ Showing {len(trades)} trades | "
            f"Total P/L: ${total_pnl:,.2f} | "
            f"Win Rate: {win_rate:.1f}%"
        )
        self.summary_label.setStyleSheet("color: #28a745; font-weight: bold;")

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        # Signal parent to reload data
        # This will be handled by main window
        self.summary_label.setText("🔄 Refreshing...")
        self.summary_label.setStyleSheet("color: #007bff; font-style: italic;")

    def _on_export_clicked(self):
        """Handle export button click."""
        if not self.current_trades:
            QMessageBox.warning(self, "No Data", "No trades to export!")
            return

        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Trades",
            f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                writer.writerow([
                    "ID", "Symbol", "Side", "Entry Price", "Exit Price",
                    "Quantity", "P/L $", "P/L %", "Confidence",
                    "Entry Time", "Exit Time", "Status"
                ])

                # Data
                for trade in self.current_trades:
                    writer.writerow([
                        trade['id'],
                        trade['symbol'],
                        trade['side'],
                        trade['entry_price'],
                        trade.get('exit_price', ''),
                        trade['quantity'],
                        trade.get('profit_loss', ''),
                        trade.get('profit_loss_percent', ''),
                        trade.get('confidence', ''),
                        trade['entry_time'].strftime("%Y-%m-%d %H:%M:%S") if trade.get('entry_time') else '',
                        trade['exit_time'].strftime("%Y-%m-%d %H:%M:%S") if trade.get('exit_time') else '',
                        trade.get('status', '')
                    ])

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(self.current_trades)} trades to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export trades:\n{str(e)}"
            )

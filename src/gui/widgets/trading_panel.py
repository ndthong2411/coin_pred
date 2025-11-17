"""Trading control panel widget."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit,
    QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings


class TradingPanel(QWidget):
    """Trading bot control panel."""

    # Signals
    start_bot_signal = pyqtSignal(str)  # mode: "paper" or "live"
    stop_bot_signal = pyqtSignal()
    manual_trade_signal = pyqtSignal(dict)  # trade params

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bot_running = False
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("🤖 Trading Bot Control")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Bot Status Group
        status_group = self._create_status_group()
        layout.addWidget(status_group)

        # Bot Control Group
        control_group = self._create_control_group()
        layout.addWidget(control_group)

        # Manual Trade Group
        manual_group = self._create_manual_trade_group()
        layout.addWidget(manual_group)

        # Log output
        log_label = QLabel("📋 Activity Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New';
                font-size: 9pt;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_output)

        # Stretch to push everything to top
        layout.addStretch()

        self.setLayout(layout)

        # Initial log
        self.add_log("System initialized. Ready to start trading bot.")

    def _create_status_group(self):
        """Create bot status group."""
        group = QGroupBox("Bot Status")
        layout = QVBoxLayout()

        # Status indicator
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))

        self.status_label = QLabel("⚫ STOPPED")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setStyleSheet("color: #6c757d;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Mode indicator
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))

        self.mode_label = QLabel("N/A")
        self.mode_label.setFont(QFont("Arial", 10))
        mode_layout.addWidget(self.mode_label)
        mode_layout.addStretch()

        layout.addLayout(mode_layout)

        # Uptime
        uptime_layout = QHBoxLayout()
        uptime_layout.addWidget(QLabel("Uptime:"))

        self.uptime_label = QLabel("00:00:00")
        self.uptime_label.setFont(QFont("Arial", 10))
        uptime_layout.addWidget(self.uptime_label)
        uptime_layout.addStretch()

        layout.addLayout(uptime_layout)

        group.setLayout(layout)
        return group

    def _create_control_group(self):
        """Create bot control group."""
        group = QGroupBox("Bot Control")
        layout = QVBoxLayout()

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Trading Mode:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Paper Trading", "Live Trading"])
        self.mode_combo.setCurrentIndex(0)
        mode_layout.addWidget(self.mode_combo)

        layout.addLayout(mode_layout)

        # Start/Stop buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("▶️ Start Bot")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.start_button.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏸️ Stop Bot")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def _create_manual_trade_group(self):
        """Create manual trade group."""
        group = QGroupBox("Manual Trade (Advanced)")
        group.setCheckable(True)
        group.setChecked(False)

        form_layout = QFormLayout()

        # Symbol selection
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(settings.trading.target_symbols)
        form_layout.addRow("Symbol:", self.symbol_combo)

        # Side selection
        self.side_combo = QComboBox()
        self.side_combo.addItems(["BUY", "SELL"])
        form_layout.addRow("Side:", self.side_combo)

        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setDecimals(6)
        self.quantity_spin.setMinimum(0.000001)
        self.quantity_spin.setMaximum(100.0)
        self.quantity_spin.setValue(0.001)
        form_layout.addRow("Quantity:", self.quantity_spin)

        # Execute button
        execute_btn = QPushButton("🚀 Execute Manual Trade")
        execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        execute_btn.clicked.connect(self._on_manual_trade_clicked)
        form_layout.addRow("", execute_btn)

        group.setLayout(form_layout)
        return group

    def _on_start_clicked(self):
        """Handle start button click."""
        # Get mode
        mode_text = self.mode_combo.currentText()
        mode = "paper" if "Paper" in mode_text else "live"

        # Confirm if live trading
        if mode == "live":
            reply = QMessageBox.question(
                self,
                "⚠️ Confirm Live Trading",
                "You are about to start LIVE TRADING with REAL MONEY!\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

        # Emit signal
        self.start_bot_signal.emit(mode)

        # Update UI
        self.bot_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.mode_combo.setEnabled(False)

        self.status_label.setText("🟢 RUNNING")
        self.status_label.setStyleSheet("color: #28a745;")
        self.mode_label.setText(mode.upper())

        self.add_log(f"✅ Bot started in {mode.upper()} mode")

    def _on_stop_clicked(self):
        """Handle stop button click."""
        # Emit signal
        self.stop_bot_signal.emit()

        # Update UI
        self.bot_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.mode_combo.setEnabled(True)

        self.status_label.setText("⚫ STOPPED")
        self.status_label.setStyleSheet("color: #6c757d;")
        self.mode_label.setText("N/A")
        self.uptime_label.setText("00:00:00")

        self.add_log("⏸️ Bot stopped")

    def _on_manual_trade_clicked(self):
        """Handle manual trade button click."""
        trade_params = {
            'symbol': self.symbol_combo.currentText(),
            'side': self.side_combo.currentText(),
            'quantity': self.quantity_spin.value()
        }

        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Manual Trade",
            f"Execute {trade_params['side']} {trade_params['quantity']} "
            f"{trade_params['symbol']}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.manual_trade_signal.emit(trade_params)
            self.add_log(f"🚀 Manual trade: {trade_params['side']} {trade_params['quantity']} {trade_params['symbol']}")

    def add_log(self, message: str):
        """Add message to log output."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_uptime(self, uptime_str: str):
        """Update uptime display."""
        self.uptime_label.setText(uptime_str)

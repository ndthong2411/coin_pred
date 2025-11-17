#!/usr/bin/env python
"""
Main entry point for Desktop GUI Application.

Usage:
    python main_gui.py
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gui.main_window import MainWindow
from src.utils import log
from config import settings


def create_splash_screen(app):
    """Create a splash screen for startup."""
    # Create a simple splash screen
    splash_pix = QPixmap(600, 400)
    splash_pix.fill(QColor("#667eea"))

    painter = QPainter(splash_pix)
    painter.setPen(QColor("white"))

    # Title
    title_font = QFont("Arial", 24, QFont.Bold)
    painter.setFont(title_font)
    painter.drawText(splash_pix.rect(), Qt.AlignCenter, "🚀 Crypto Trading Bot\n\nProfessional Edition")

    # Subtitle
    subtitle_font = QFont("Arial", 12)
    painter.setFont(subtitle_font)
    painter.drawText(50, 350, "Loading application...")

    painter.end()

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())

    return splash


def main():
    """Main entry point."""
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Crypto Trading Bot")
        app.setOrganizationName("CryptoBot")

        # Set application style
        app.setStyle('Fusion')

        # Show splash screen
        splash = create_splash_screen(app)
        splash.show()
        app.processEvents()

        # Log startup
        log.info("=" * 60)
        log.info("CRYPTO TRADING BOT - DESKTOP APPLICATION")
        log.info("=" * 60)
        log.info(f"Version: 2.0")
        log.info(f"Mode: {settings.trading.trading_mode.upper()}")
        log.info(f"Symbols: {', '.join(settings.trading.target_symbols)}")
        log.info("=" * 60)

        # Create main window
        splash.showMessage(
            "Initializing main window...",
            Qt.AlignBottom | Qt.AlignCenter,
            QColor("white")
        )
        app.processEvents()

        main_window = MainWindow()

        # Close splash and show main window
        splash.finish(main_window)
        main_window.show()

        log.info("✅ Desktop application started successfully!")
        log.info("Main window displayed")

        # Run application
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        log.info("\n⚠️  Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        log.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

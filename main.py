"""
Микроникс — PyQt6 application
Main entry point
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import MicronixMainWindow
from styles import apply_theme


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application-wide style
    app.setStyle("Fusion")

    # Единая тема на уровне приложения (QSS в styles.py)
    apply_theme(app)

    # Create and show main window
    window = MicronixMainWindow()
    window.show()

    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

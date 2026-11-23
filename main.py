"""
Микроникс — PyQt6 application
Main entry point
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import MicronixMainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application-wide style
    app.setStyle("Fusion")

    # Стиль для рамки окна
    app.setStyleSheet("""
        QMainWindow {
            background: transparent;
        }

        QWidget#central_widget {
            background: #222326;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Эффект тени */
        QGraphicsDropShadowEffect {
            border-radius: 12px;
            color: rgba(0, 0, 0, 0.3);
            blur-radius: 20px;
        }
    """)

    # Глобальный темный стиль для всех виджетов
    dark_style = """
    /* Основной фон для всех виджетов */
    QMainWindow, QDialog, QWidget {
        background: transparent;
    }

    QLabel, QPushButton {
        color: white;
    }

    /* Специально для фонового виджета */
    GradientBackground {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #222326, stop:1 #191a1d);
    }

    /* Панель - ПОЛНОСТЬЮ НЕПРОЗРАЧНАЯ */
    SlideInPanel {
        background: #1a1b1e;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Карточки */
    ModernCard {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(255, 255, 255, 0.1),
            stop:1 rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }

    /* Таблицы */
    QTableWidget {
        background: rgba(30, 31, 34, 0.9);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }

    /* Поля ввода */
    QLineEdit, QSpinBox, QComboBox, QTextEdit {
        background: rgba(40, 41, 44, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        padding: 8px 12px;
        color: white;
        selection-background-color: rgba(120, 121, 241, 0.5);
    }

    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid rgba(120, 121, 241, 0.6);
    }

    /* Кнопки в сайдбаре */
    QPushButton {
        background: transparent;
        border: none;
        text-align: left;
        padding: 12px 20px;
    }

    /* Заголовки секций */
    QGroupBox {
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        margin-top: 16px;
        padding-top: 10px;
        background: rgba(40, 41, 44, 0.6);
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px;
    }

    /* Скроллбары */
    QScrollBar:vertical {
        background: rgba(255, 255, 255, 0.05);
        width: 10px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 5px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    /* Разделители */
    QSplitter::handle {
        background: rgba(255, 255, 255, 0.1);
    }

    QSplitter::handle:hover {
        background: rgba(120, 121, 241, 0.3);
    }
    """
    app.setStyleSheet(dark_style)

    # Create and show main window
    window = MicronixMainWindow()
    window.show()

    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
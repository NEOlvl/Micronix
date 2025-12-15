"""
Method card widget with modern design
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtGui import QFont
from .modern_card import ModernCard
from styles import Styles


class MethodCard(ModernCard):
    """Method selection card with number in top-left corner"""

    clicked = pyqtSignal()  # Сигнал при клике на карточку

    def __init__(self, method_num, method_name, method_title, icon="📡", color=None, parent=None):
        super().__init__(parent)
        self.method_num = method_num
        self.icon = icon
        self.color = color or Styles.PRIMARY
        self.setup_ui(method_num, method_name, method_title, icon, color)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Начальный стиль
        self.setStyleSheet(f"""
            MethodCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 41, 44, 0.9),
                    stop:1 rgba(30, 31, 34, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }}
        """)

    def setup_ui(self, method_num, method_name, method_title, icon, color):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header с номером метода
        header_widget = QWidget()
        header_widget.setFixedHeight(40)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 0, 15, 0)

        # Номер метода в левом верхнем углу
        number_label = QLabel(f"{method_num}")
        number_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                font-family: 'Arial', sans-serif;
            }}
        """)

        header_layout.addWidget(number_label)
        header_layout.addStretch()

        layout.addWidget(header_widget)

        # Main content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 5, 15, 20)
        content_layout.setSpacing(10)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 32px;
                background: transparent;
                margin-top: 5px;
            }}
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(icon_label)

        # Method name (big)
        name_label = QLabel(method_name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
                text-align: center;
                font-family: 'Arial', sans-serif;
            }}
        """)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(name_label)

        # Method title (description)
        title_label = QLabel(method_title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: normal;
                background: transparent;
                text-align: center;
                line-height: 1.4;
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)

        # Spacer
        content_layout.addStretch()

        layout.addWidget(content_widget)

    def mousePressEvent(self, event):
        """При клике на карточку"""
        super().mousePressEvent(event)
        self.clicked.emit()
        self.animate_click()

    def enterEvent(self, event):
        # При наведении - меняем цвет рамки
        self.setStyleSheet(f"""
            MethodCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 51, 54, 0.95),
                    stop:1 rgba(40, 41, 44, 0.95));
                border: 2px solid {self.color};
                border-radius: 12px;
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Возвращаем исходный стиль
        self.setStyleSheet(f"""
            MethodCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 41, 44, 0.9),
                    stop:1 rgba(30, 31, 34, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }}
        """)
        super().leaveEvent(event)

    def animate_click(self):
        """Simple click animation"""
        from PyQt6.QtCore import QTimer

        # Эффект нажатия
        self.setStyleSheet(f"""
            MethodCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 61, 64, 0.95),
                    stop:1 rgba(50, 51, 54, 0.95));
                border: 2px solid {self.color};
                border-radius: 12px;
            }}
        """)

        # Возвращаемся через 150ms
        QTimer.singleShot(150, lambda: self.leaveEvent(None))
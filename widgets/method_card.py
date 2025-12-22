"""
Method card widget with modern design - UPDATED VERSION for smaller cards
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSpacerItem, QSizePolicy
from .modern_card import ModernCard
from styles import Styles


class MethodCard(ModernCard):
    """Method selection card with image on the right and categories only"""

    clicked = pyqtSignal()  # Сигнал при клике на карточку

    def __init__(self, method_num, method_name, method_title, category="Диэлектрики", color=None, parent=None):
        super().__init__(parent)
        self.method_num = method_num
        self.category = category  # "Диэлектрики" или "Ферриты"
        self.color = color or Styles.PRIMARY

        self.setup_ui(method_num, method_name, method_title, category, color)
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

    def setup_ui(self, method_num, method_name, method_title, category, color):
        # Главный layout - горизонтальный
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Отступы
        main_layout.setSpacing(15)

        # ЛЕВАЯ ЧАСТЬ: Только текст с названием метода
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)  # Без spacing между элементами

        # Название метода - занимает всё доступное пространство сверху
        name_label = QLabel(method_name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                font-family: 'Arial', sans-serif;
                line-height: 1.3;
            }}
        """)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Spacer между названием и категорией
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Категория внизу
        category_color = "#7879F1" if category == "Диэлектрики" else "#FF6B6B"
        category_label = QLabel(category)
        category_label.setStyleSheet(f"""
            QLabel {{
                color: {category_color};
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                text-transform: uppercase;
                padding-top: 5px;
                border-top: 1px solid {category_color};
            }}
        """)
        category_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        # Добавляем элементы в layout
        text_layout.addWidget(name_label)
        text_layout.addSpacerItem(spacer)  # Spacer выталкивает категорию вниз
        text_layout.addWidget(category_label)

        # ПРАВАЯ ЧАСТЬ: Пустое пространство или минимальный индикатор
        right_container = QWidget()
        right_container.setFixedSize(150, 120)
        right_container.setStyleSheet(f"""
            QWidget {{
                background: {category_color};
                border-radius: 6px;
                opacity: 0.7;
            }}
        """)

        main_layout.addWidget(text_container, 1)  # Занимает всё доступное пространство
        main_layout.addWidget(right_container)

    def mousePressEvent(self, event):
        """При клике на карточку"""
        super().mousePressEvent(event)
        self.clicked.emit()
        self.animate_click()

    def enterEvent(self, event):
        """При наведении - меняем цвет рамки"""
        hover_color = "#7879F1"  # Фиолетовый цвет при наведении
        self.setStyleSheet(f"""
            MethodCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 51, 54, 0.95),
                    stop:1 rgba(40, 41, 44, 0.95));
                border: 2px solid {hover_color};
                border-radius: 12px;
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Возвращаем исходный стиль"""
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
        hover_color = "#7879F1"
        self.setStyleSheet(f"""
            MethodCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 61, 64, 0.95),
                    stop:1 rgba(50, 51, 54, 0.95));
                border: 2px solid {hover_color};
                border-radius: 12px;
            }}
        """)

        # Возвращаемся через 150ms
        QTimer.singleShot(150, lambda: self.leaveEvent(None))
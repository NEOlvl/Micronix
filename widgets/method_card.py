"""
Method card widget - карточка выбора метода.

Стиль задаётся единой темой (MethodCard / MethodCard:hover
в APP_QSS), интерактивные состояния — псевдо-состояниями QSS.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSpacerItem, QSizePolicy
from PyQt6.QtSvgWidgets import QSvgWidget
import os
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

    def setup_ui(self, method_num, method_name, method_title, category, color):
        # Главный layout - горизонтальный
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ЛЕВАЯ ЧАСТЬ: Только текст с названием метода
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        # Название метода
        name_label = QLabel(method_name)
        name_label.setProperty("role", "methodName")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Spacer между названием и категорией
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Категория внизу
        category_label = QLabel(category)
        category_label.setProperty("role", "methodCategory")
        category_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        # Добавляем элементы в layout
        text_layout.addWidget(name_label)
        text_layout.addSpacerItem(spacer)
        text_layout.addWidget(category_label)

        # ПРАВАЯ ЧАСТЬ: SVG изображение в зависимости от категории
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        svg_filename = "method_dielectr.svg" if category == "Диэлектрики" else "method_ferr.svg"
        svg_path = os.path.join("img", svg_filename)

        if os.path.exists(svg_path):
            svg_widget = QSvgWidget(svg_path)
        else:
            # Альтернатива: текстовая иконка
            svg_widget = QLabel("⚡" if category == "Диэлектрики" else "🧲")
            svg_widget.setStyleSheet(
                "QLabel { font-size: 48px; background: transparent; }")
            svg_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        svg_widget.setFixedSize(120, 120)

        right_layout.addStretch()
        right_layout.addWidget(svg_widget)
        right_layout.addStretch()

        main_layout.addWidget(text_container, 1)
        main_layout.addWidget(right_container)

    def mousePressEvent(self, event):
        """При клике на карточку"""
        super().mousePressEvent(event)
        self.clicked.emit()

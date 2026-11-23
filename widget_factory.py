"""
Widget factory for creating common UI components.

Виджеты помечаются свойствами (role / btnStyle), а стили
приходят из единого APP_QSS (styles.py) — без инлайн-стилей.
"""

from PyQt6.QtWidgets import (QLabel, QPushButton, QLineEdit, QVBoxLayout,
                             QHBoxLayout, QFrame, QScrollArea, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt
from styles import Styles


class WidgetFactory:
    """Factory for creating styled widgets"""

    # Соответствие font_size -> роль в QSS
    _SIZE_ROLES = {22: "h1", 24: "h1", 17: "h2", 18: "h2", 15: "h3", 16: "h3"}

    @staticmethod
    def create_label(text, font_size=14, color=None, bold=False, align=None,
                     role=None):
        label = QLabel(text)

        if role is not None:
            # Роль из глобальной темы — без инлайн-стилей
            label.setProperty("role", role)
        else:
            # Нестандартная комбинация — точечный инлайн-стиль
            style_parts = [f"color: {color or Styles.TEXT_PRIMARY}",
                           f"font-size: {font_size}px",
                           "background: transparent"]
            if bold:
                style_parts.append("font-weight: 600")
            label.setStyleSheet("; ".join(style_parts) + ";")

        # Set alignment if specified
        if align:
            alignment_map = {
                "center": Qt.AlignmentFlag.AlignCenter,
                "right": Qt.AlignmentFlag.AlignRight,
                "left": Qt.AlignmentFlag.AlignLeft
            }
            if align in alignment_map:
                label.setAlignment(alignment_map[align])

        return label

    @staticmethod
    def create_title(text, level=1):
        """Create title with different levels (h1, h2, h3)"""
        return WidgetFactory.create_label(text, role=f"h{level}")

    @staticmethod
    def create_button(text, style="primary", icon=None, size=None):
        btn = QPushButton(text)
        btn.setProperty("btnStyle", style)

        if icon:
            btn.setIcon(icon)

        # Set size if specified
        if size:
            if isinstance(size, tuple) and len(size) == 2:
                btn.setFixedSize(size[0], size[1])
            elif isinstance(size, int):
                btn.setFixedHeight(size)

        return btn

    @staticmethod
    def create_input(placeholder="", style=None):
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        return input_field

    @staticmethod
    def create_combo(items=None):
        combo = QComboBox()
        if items:
            combo.addItems(items)
        return combo

    @staticmethod
    def create_spinbox(min_val=0, max_val=100, default=0):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        return spin

    @staticmethod
    def create_card(content_widget=None, layout_type="vertical", margins=20):
        """Create a ModernCard with optional content"""
        from widgets import ModernCard

        card = ModernCard()

        if content_widget:
            if layout_type == "vertical":
                layout = QVBoxLayout(card)
            else:
                layout = QHBoxLayout(card)

            layout.setContentsMargins(margins, margins, margins, margins)
            layout.addWidget(content_widget)

        return card

    @staticmethod
    def create_divider(vertical=False):
        """Create a styled divider line"""
        divider = QFrame()
        divider.setObjectName("divider")
        if vertical:
            divider.setFrameShape(QFrame.Shape.VLine)
            divider.setFixedWidth(1)
        else:
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setFixedHeight(1)

        return divider

    @staticmethod
    def create_scroll_area(widget=None):
        """Create a styled scroll area"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        if widget:
            scroll.setWidget(widget)

        return scroll

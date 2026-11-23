"""
Sidebar widget - навигация с единой темой (btnStyle="nav").
"""

import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy)
from PyQt6.QtSvgWidgets import QSvgWidget
from styles import Styles, repolish


def _img_path(filename):
    """Путь к файлу в папке img от корня проекта."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "img", filename)


class SidebarWidget(QWidget):
    """Main sidebar navigation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(260)
        self.active_button = None
        self.icon_size = 24
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with logo
        header = self.create_header()
        layout.addWidget(header)

        # Main navigation
        self.setup_main_navigation(layout)

        # Spacer between main nav and footer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Footer with settings and user
        self.setup_footer(layout)

    def create_header(self):
        """Create stylish header with logo"""
        header = QFrame()
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(100)

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)
        header_layout.setSpacing(8)

        # Logo with icon
        logo_layout = QHBoxLayout()

        icon_widget = self.load_svg("menu-burger.svg", size=28)
        if isinstance(icon_widget, QSvgWidget):
            icon_container = QWidget()
            icon_container.setFixedSize(28, 28)
            icon_layout = QVBoxLayout(icon_container)
            icon_layout.setContentsMargins(0, 0, 0, 0)
            icon_layout.addWidget(icon_widget)
            logo_layout.addWidget(icon_container)
        else:
            logo_layout.addWidget(icon_widget)

        # Logo text
        logo_text = QLabel(" MICRONIX")
        logo_text.setProperty("role", "logo")
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()

        # Subtitle
        subtitle = QLabel("Измерительная система")
        subtitle.setProperty("role", "logoSub")
        subtitle.setContentsMargins(36, 0, 0, 0)

        header_layout.addLayout(logo_layout)
        header_layout.addWidget(subtitle)

        return header

    def setup_main_navigation(self, parent_layout):
        """Setup main navigation items"""
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(15, 20, 15, 20)
        nav_layout.setSpacing(2)

        nav_items = [
            ("Главная", "home.svg"),
            ("Новое исследование", "plan.svg"),
            ("Измерения", "metric.svg"),
            ("Отчёты", "document.svg")
        ]

        self.nav_buttons = []
        for i, (text, icon_filename) in enumerate(nav_items):
            btn = self.create_nav_button(text, icon_filename)
            btn.setProperty("nav_index", i)
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

            # Set first button as active by default
            if i == 0:
                self.set_active_button(btn)

        nav_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        parent_layout.addWidget(nav_container)

    def load_svg(self, filename, size=None):
        """Загрузка SVG изображения из папки img как виджет."""
        if size is None:
            size = self.icon_size

        svg_path = _img_path(filename)

        if os.path.exists(svg_path):
            svg_widget = QSvgWidget(svg_path)
            svg_widget.setFixedSize(size, size)
            return svg_widget

        # Fallback: текстовый символ
        fallback_text = {
            "home.svg": "🏠",
            "metric.svg": "📊",
            "document.svg": "📄",
            "menu-burger.svg": "☰",
            "users.svg": "👤",
            "settings.svg": "⚙",
            "plan.svg": "📋"
        }
        label = QLabel(fallback_text.get(filename, "📁"))
        label.setProperty("role", "imagePlaceholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def load_icon(self, filename, size=20):
        """Иконка для кнопки: QIcon из SVG или None."""
        svg_path = _img_path(filename)
        if os.path.exists(svg_path):
            return QIcon(svg_path)
        return None

    def create_nav_button(self, text, icon_filename):
        """Create a navigation button (иконка + текст через QSS)."""
        btn = QPushButton(text)
        btn.setProperty("btnStyle", "nav")
        btn.setProperty("active", False)
        btn.setFixedHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        icon = self.load_icon(icon_filename)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(QSize(20, 20))

        return btn

    def setup_footer(self, parent_layout):
        """Setup footer with settings and user info"""
        footer = QFrame()
        footer.setObjectName("sidebarFooter")
        footer.setFixedHeight(150)

        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(15, 20, 15, 20)
        footer_layout.setSpacing(15)

        # User info
        user_widget = self.create_user_widget()
        footer_layout.addWidget(user_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("divider")
        separator.setFixedHeight(1)
        footer_layout.addWidget(separator)

        # Settings button
        settings_btn = self.create_settings_button()
        footer_layout.addWidget(settings_btn)

        parent_layout.addWidget(footer)

    def create_user_widget(self):
        """Create user info widget с SVG иконкой"""
        user_widget = QWidget()

        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(5, 0, 5, 0)
        user_layout.setSpacing(12)

        # User avatar
        avatar_widget = self.load_svg("users.svg", size=28)

        # Текст
        text_label = QLabel("Пользователь")
        text_label.setProperty("role", "userName")

        # Role
        role_label = QLabel("Оператор")
        role_label.setProperty("role", "caption")

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(text_label)
        text_layout.addWidget(role_label)

        user_layout.addWidget(avatar_widget)
        user_layout.addLayout(text_layout)
        user_layout.addStretch()

        return user_widget

    def create_settings_button(self):
        """Create settings button с иконкой"""
        btn = self.create_nav_button("Настройки", "settings.svg")
        btn.setFixedHeight(44)
        return btn

    def set_active_button(self, button):
        """Set button as active (highlighted)"""
        if self.active_button is button:
            return
        if self.active_button:
            self.active_button.setProperty("active", False)
            repolish(self.active_button)

        button.setProperty("active", True)
        repolish(button)
        self.active_button = button

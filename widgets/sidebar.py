"""
Sidebar widget - красивая версия с фиолетовой цветовой схемой
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy)
from PyQt6.QtSvgWidgets import QSvgWidget
import os
from styles import Styles


class SidebarWidget(QWidget):
    """Main sidebar navigation - красивая версия"""

    def __init__(self, parent=None):
        super().__init__(parent)
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
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.PRIMARY},
                    stop:1 {Styles.PRIMARY});
                border-bottom: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)
        header.setFixedHeight(100)

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)
        header_layout.setSpacing(8)

        # Logo with icon
        logo_layout = QHBoxLayout()

        # Logo icon - SVG из папки img
        icon_widget = self.load_svg("menu-burger.svg", size=28)

        # Если это QSvgWidget, нужно обернуть его в QWidget для центрирования
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
        logo_text.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Arial';
                background: transparent;
                letter-spacing: 1px;
                text-decoration: none;
                border: none;
                padding: 0;
            }
        """)
        logo_text.setProperty("class", "logo-text")

        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()

        # Subtitle
        subtitle = QLabel("Измерительная система")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 400;
                background: transparent;
                padding-left: 36px;
                text-decoration: none;
                border: none;
            }}
        """)
        subtitle.setProperty("class", "logo-subtitle")

        header_layout.addLayout(logo_layout)
        header_layout.addWidget(subtitle)

        return header

    def setup_main_navigation(self, parent_layout):
        """Setup main navigation items"""
        # Container for navigation items
        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")

        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(15, 20, 15, 20)
        nav_layout.setSpacing(2)

        # Основная фиолетовая палитра - разные оттенки
        colors = {
            "main": Styles.PRIMARY,  # #7879F1
            "light": Styles.PRIMARY_LIGHT,  # #9A9BFF
            "violet": "#9D7BF1",  # Более светлый фиолетовый
            "lavender": "#B19BFF",  # Лавандовый
        }

        # Main navigation items с SVG иконками
        nav_items = [
            ("Главная", "home.svg", colors["main"]),
            ("Новое исследование", "plan.svg", colors["main"]),
            ("Измерения", "metric.svg", colors["main"]),
            ("Отчёты", "document.svg", colors["main"])
        ]

        self.nav_buttons = []
        for i, (text, icon_filename, color) in enumerate(nav_items):
            btn = self.create_nav_button(text, icon_filename, color)
            btn.setProperty("nav_index", i)
            btn.setProperty("button_color", color)  # Сохраняем цвет в свойствах
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

            # Set first button as active by default
            if i == 0:
                self.set_active_button(btn)

        # Add some spacing
        nav_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        parent_layout.addWidget(nav_container)

    def load_svg(self, filename, size=None):
        """Загрузка SVG изображения из папки img"""
        if size is None:
            size = self.icon_size

        # Получаем корень проекта (на один уровень выше widgets)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        svg_path = os.path.join(project_root, "img", filename)

        if os.path.exists(svg_path):
            svg_widget = QSvgWidget(svg_path)
            svg_widget.setFixedSize(size, size)
            svg_widget.setStyleSheet("QSvgWidget { background: transparent; }")
            return svg_widget
        else:
            # Fallback: создаем QLabel с текстовым символом
            fallback_text = {
                "home.svg": "🏠",
                "metric.svg": "📊",
                "document.svg": "📄",
                "menu-burger.svg": "☰",
                "users.svg": "👤",  # Для пользователя
                "settings.svg": "⚙",  # Для настроек
                "plan.svg": "📋"  # Для "Новое исследование"
            }
            label = QLabel(fallback_text.get(filename, "📁"))
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: {size}px;
                    background: transparent;
                    color: {Styles.TEXT_SECONDARY};
                }}
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label

    def create_nav_button(self, text, icon_filename, color):
        """Create a stylish navigation button"""
        # Создаем пустую кнопку без текста
        btn = QPushButton()
        btn.setFixedHeight(52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Создаем layout для кнопки с иконкой
        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(20, 0, 20, 0)
        btn_layout.setSpacing(12)

        # Загружаем SVG иконку
        icon_widget = self.load_svg(icon_filename)

        # Если это QSvgWidget, нужно обернуть его для центрирования
        if isinstance(icon_widget, QSvgWidget):
            icon_container = QWidget()
            icon_container.setFixedSize(self.icon_size, self.icon_size)
            icon_container_layout = QVBoxLayout(icon_container)
            icon_container_layout.setContentsMargins(0, 0, 0, 0)
            icon_container_layout.addWidget(icon_widget)
            btn_layout.addWidget(icon_container)
        else:
            btn_layout.addWidget(icon_widget)

        # Текст
        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }}
        """)

        btn_layout.addWidget(text_label)
        btn_layout.addStretch()

        # Base style
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                text-align: left;
                padding: 0;
                border-radius: 10px;
                margin: 2px 5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
        """)

        return btn

    def setup_footer(self, parent_layout):
        """Setup footer with settings and user info"""
        footer = QFrame()
        footer.setFixedHeight(150)
        footer.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-top: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)

        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(15, 20, 15, 20)
        footer_layout.setSpacing(15)

        # User info
        user_widget = self.create_user_widget()
        footer_layout.addWidget(user_widget)

        # Separator - оставляем эту линию (между пользователем и настройками)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background: {Styles.BORDER_LIGHT};")
        separator.setFixedHeight(1)
        footer_layout.addWidget(separator)

        # Settings button - используем эмодзи
        settings_btn = self.create_settings_button()
        footer_layout.addWidget(settings_btn)

        parent_layout.addWidget(footer)

    def create_user_widget(self):
        """Create user info widget с SVG иконкой"""
        user_widget = QWidget()
        user_widget.setStyleSheet("background: transparent;")

        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(5, 0, 5, 0)
        user_layout.setSpacing(12)

        # User avatar - SVG из папки img
        avatar_widget = self.load_svg("users.svg", size=28)  # Заменяем эмодзи на SVG

        # УБИРАЕМ контейнер с фиолетовым фоном - просто добавляем иконку
        # Текст
        text_label = QLabel("Пользователь")
        text_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                text-decoration: none;
                border: none;
                padding: 0;
            }}
        """)

        # Role
        role_label = QLabel("Оператор")
        role_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 400;
                background: transparent;
                text-decoration: none;
                border: none;
                padding: 0;
            }}
        """)

        # Создаем layout для текста
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
        """Create settings button с SVG иконкой"""
        # Создаем пустую кнопку
        btn = QPushButton()
        btn.setFixedHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Создаем layout для кнопки
        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(20, 0, 20, 0)
        btn_layout.setSpacing(12)

        # SVG иконка для настроек
        icon_widget = self.load_svg("settings.svg", size=self.icon_size)

        # Для QSvgWidget не вызываем setAlignment
        # Для QLabel (fallback) setAlignment уже вызван в load_svg()

        # Текст
        text_label = QLabel("Настройки")
        text_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }}
        """)

        btn_layout.addWidget(icon_widget)
        btn_layout.addWidget(text_label)
        btn_layout.addStretch()

        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.05);
                color: {Styles.TEXT_SECONDARY};
                border: 1px solid {Styles.BORDER_LIGHT};
                text-align: left;
                padding: 0;
                font-size: 14px;
                font-weight: 500;
                border-radius: 10px;
                margin: 2px 5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {Styles.PRIMARY};
            }}
        """)

        return btn

    def set_active_button(self, button):
        """Set button as active (highlighted)"""
        if self.active_button:
            # Reset previous active button
            if hasattr(self.active_button, 'text_label'):
                self.active_button.text_label.setStyleSheet(f"""
                    QLabel {{
                        color: {Styles.TEXT_SECONDARY};
                        font-size: 14px;
                        font-weight: 500;
                        background: transparent;
                    }}
                """)

            self.active_button.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    text-align: left;
                    padding: 0;
                    border-radius: 10px;
                    margin: 2px 5px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.05);
                }}
            """)

        # Get button color from its property
        color = button.property("button_color")
        if not color:
            # Fallback to primary light
            color = Styles.PRIMARY_LIGHT

        # Highlight new active button
        if hasattr(button, 'text_label'):
            button.text_label.setStyleSheet(f"""
                QLabel {{
                    color: {Styles.TEXT_PRIMARY};
                    font-size: 14px;
                    font-weight: 600;
                    background: transparent;
                }}
            """)

        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border: 1px solid {color};
                text-align: left;
                padding: 0;
                border-radius: 10px;
                margin: 2px 5px;
            }}
            QPushButton:hover {{
                background: {color};
            }}
        """)

        self.active_button = button
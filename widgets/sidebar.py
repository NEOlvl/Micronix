"""
Sidebar widget - красивая версия с фиолетовой цветовой схемой
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy)
from styles import Styles


class SidebarWidget(QWidget):
    """Main sidebar navigation - красивая версия"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.active_button = None
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

        # Logo icon - микроволновая печь/антенна
        icon_label = QLabel("⚡")
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.PRIMARY_LIGHT};
                font-size: 28px;
                background: transparent;
                text-decoration: none;
                border: none;
                padding: 0;
            }}
        """)
        icon_label.setProperty("class", "logo-icon")

        # Logo text
        logo_text = QLabel("FERRO")
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

        logo_layout.addWidget(icon_label)
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

        # Main navigation items с иконками и оттенками фиолетового
        nav_items = [
            ("Главная", "🏠", colors["main"]),
            ("Новое исследование", "⚡", colors["main"]),
            ("Измерения", "📊", colors["main"]),
            ("Отчёты", "📄", colors["main"])
        ]

        self.nav_buttons = []
        for i, (text, icon, color) in enumerate(nav_items):
            btn = self.create_nav_button(text, icon, color)
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

    def create_nav_button(self, text, icon, color):
        """Create a stylish navigation button"""
        btn = QPushButton(f"  {icon}  {text}")
        btn.setFixedHeight(52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Base style
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Styles.TEXT_SECONDARY};
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 10px;
                margin: 2px 5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.05);
                color: {color};
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

        # Settings button
        settings_btn = self.create_settings_button()
        footer_layout.addWidget(settings_btn)

        parent_layout.addWidget(footer)

    def create_user_widget(self):
        """Create user info widget"""
        user_widget = QWidget()
        user_widget.setStyleSheet("background: transparent;")

        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(5, 0, 5, 0)
        user_layout.setSpacing(12)

        # User avatar
        avatar = QLabel("👤")
        avatar.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                background: {Styles.PRIMARY};
                border-radius: 20px;
                padding: 8px;
                min-width: 40px;
                min-height: 40px;
                max-width: 40px;
                max-height: 40px;
            }}
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # User info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        user_name = QLabel("Пользователь")
        user_name.setStyleSheet(f"""
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

        user_role = QLabel("Оператор")
        user_role.setStyleSheet(f"""
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

        info_layout.addWidget(user_name)
        info_layout.addWidget(user_role)

        user_layout.addWidget(avatar)
        user_layout.addWidget(info_widget)
        user_layout.addStretch()

        return user_widget

    def create_settings_button(self):
        """Create settings button"""
        btn = QPushButton("  ⚙  Настройки")
        btn.setFixedHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.05);
                color: {Styles.TEXT_SECONDARY};
                border: 1px solid {Styles.BORDER_LIGHT};
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 10px;
                margin: 2px 5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                color: {Styles.PRIMARY_LIGHT};
                border: 1px solid {Styles.PRIMARY};
            }}
        """)

        return btn

    def set_active_button(self, button):
        """Set button as active (highlighted)"""
        if self.active_button:
            # Reset previous active button
            self.active_button.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Styles.TEXT_SECONDARY};
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border-radius: 10px;
                    margin: 2px 5px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.05);
                    color: {self.active_button.property("button_color") or Styles.PRIMARY_LIGHT};
                }}
            """)

        # Get button color from its property
        color = button.property("button_color")
        if not color:
            # Fallback to primary light
            color = Styles.PRIMARY_LIGHT

        # Highlight new active button
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: {Styles.TEXT_PRIMARY};
                border: 1px solid {color};
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: 600;
                border-radius: 10px;
                margin: 2px 5px;
            }}
            QPushButton:hover {{
                background: {color};
                color: {Styles.TEXT_PRIMARY};
            }}
        """)

        self.active_button = button
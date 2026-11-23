"""
Settings page - optimized version
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QComboBox,
                             QCheckBox, QGroupBox)
from pages.base_page import BasePage
from widget_factory import WidgetFactory


class SettingsPage(BasePage):
    """Settings page - optimized"""

    def __init__(self, parent=None):
        super().__init__("Настройки", "", parent)

        # Clear default layout
        self.clear_layout()

        # Setup UI
        self.setup_sidebar()
        self.setup_content_area()

    def clear_layout(self):
        """Clear the default layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create main horizontal layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

    def setup_sidebar(self):
        """Setup sidebar menu"""
        sidebar = QWidget()
        sidebar.setObjectName("settingsSidebar")
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar.setFixedWidth(280)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Settings title
        title = WidgetFactory.create_title("Настройки", level=1)
        title.setContentsMargins(30, 25, 30, 10)
        sidebar_layout.addWidget(title)

        # Settings categories
        categories = [
            ("Основное", [
                ("Аккаунт", "account"),
                ("Интерфейс", "theme")
            ]),
            ("Внешние устройства", [
                ("Рефлектометры", "reflectometer"),
                ("Управляющие механизмы", "mechanism")
            ]),
            ("Специальное", [
                ("Разработчикам", "developer")
            ])
        ]

        for category_name, items in categories:
            # Category label
            category_label = WidgetFactory.create_label(
                category_name,
                role="navCategory"
            )
            category_label.setContentsMargins(30, 18, 30, 6)
            sidebar_layout.addWidget(category_label)

            # Category items
            for item_name, item_icon in items:
                item_btn = WidgetFactory.create_button(
                    item_name,
                    style="navSub"
                )
                item_btn.setFixedHeight(44)
                sidebar_layout.addWidget(item_btn)

        sidebar_layout.addStretch()
        self.main_layout.addWidget(sidebar)

    def setup_content_area(self):
        """Setup content area with settings form"""
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)

        # Content title
        content_title = WidgetFactory.create_title("Настройка аккаунта", level=1)
        content_layout.addWidget(content_title)

        # Create scrollable settings form
        scroll_area = WidgetFactory.create_scroll_area()
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(20)

        # Account settings section
        account_section = self.create_account_section()
        settings_layout.addWidget(account_section)

        # Interface settings section
        interface_section = self.create_interface_section()
        settings_layout.addWidget(interface_section)

        # Notifications section
        notifications_section = self.create_notifications_section()
        settings_layout.addWidget(notifications_section)

        settings_layout.addStretch()

        scroll_area.setWidget(settings_widget)
        content_layout.addWidget(scroll_area, 1)

        # Save button
        save_btn = WidgetFactory.create_button("Сохранить изменения", style="primary")
        save_btn.setFixedWidth(200)
        content_layout.addWidget(save_btn, 0, Qt.AlignmentFlag.AlignRight)

        self.main_layout.addWidget(content, 1)

    def create_account_section(self):
        """Create account settings section"""
        from widgets import ModernCard

        section = ModernCard()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(20, 20, 20, 20)
        section_layout.setSpacing(15)

        # Section title
        title = WidgetFactory.create_title("Аккаунт", level=2)
        section_layout.addWidget(title)

        # Form
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(20)

        # Name field
        name_label = WidgetFactory.create_label("Имя пользователя:")
        name_input = WidgetFactory.create_input("Введите ваше имя")
        form_layout.addRow(name_label, name_input)

        # Email field
        email_label = WidgetFactory.create_label("Email:")
        email_input = WidgetFactory.create_input("user@example.com")
        form_layout.addRow(email_label, email_input)

        # Language selector
        language_label = WidgetFactory.create_label("Язык:")
        language_combo = QComboBox()
        language_combo.addItems(["Русский", "English", "Deutsch"])
        form_layout.addRow(language_label, language_combo)

        section_layout.addLayout(form_layout)

        return section

    def create_interface_section(self):
        """Create interface settings section"""
        from widgets import ModernCard

        section = ModernCard()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(20, 20, 20, 20)
        section_layout.setSpacing(15)

        # Section title
        title = WidgetFactory.create_title("Интерфейс", level=2)
        section_layout.addWidget(title)

        # Theme selector
        theme_group = QGroupBox("Тема")
        theme_layout = QVBoxLayout(theme_group)

        dark_theme = QCheckBox("Темная тема")
        light_theme = QCheckBox("Светлая тема")
        dark_theme.setChecked(True)

        theme_layout.addWidget(dark_theme)
        theme_layout.addWidget(light_theme)

        section_layout.addWidget(theme_group)

        # Animation toggle
        animations_check = QCheckBox("Включить анимации")
        animations_check.setChecked(True)
        section_layout.addWidget(animations_check)

        return section

    def create_notifications_section(self):
        """Create notifications settings section"""
        from widgets import ModernCard

        section = ModernCard()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(20, 20, 20, 20)
        section_layout.setSpacing(15)

        # Section title
        title = WidgetFactory.create_title("Уведомления", level=2)
        section_layout.addWidget(title)

        # Notification toggles
        email_check = QCheckBox("Email уведомления")
        email_check.setChecked(True)

        push_check = QCheckBox("Push-уведомления")
        push_check.setChecked(True)

        sounds_check = QCheckBox("Звуковые уведомления")

        # Style checkboxes — из единой темы
        for checkbox in [email_check, push_check, sounds_check]:
            section_layout.addWidget(checkbox)

        return section
"""
Enhanced Header Widget with optional breadcrumbs
"""

from typing import Optional, List, Tuple, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from widget_factory import WidgetFactory
from styles import Styles
from widgets.animated_button import AnimatedButton


class HeaderWidget(QWidget):
    """Enhanced page header with breadcrumbs and actions"""

    # Статические данные для лучшей организации
    STATUS_ICONS = {
        'success': '🟢',
        'warning': '🟡',
        'error': '🔴',
        'loading': '⏳',
        'info': 'ℹ️'
    }

    # Конфигурация кнопок
    MAIN_ACTION_TEXT = "Новое исследование"
    ACTION_BUTTON_STYLES = {
        'primary': """
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6A6BE1, stop:1 #8A8BEF);
            }}
        """,
        'secondary': """
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """
    }

    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        """
        Constructor for backward compatibility
        """
        super().__init__(parent)
        self._init_variables()
        # ФИКС: не передаем subtitle дальше, если он содержит "исследование" в любом регистре
        normalized_subtitle = subtitle.lower() if subtitle else ""
        if "исследование" in normalized_subtitle:
            self.setup_ui(title, "", breadcrumbs=None)
        else:
            self.setup_ui(title, subtitle, breadcrumbs=None)

    def _init_variables(self):
        """Initialize instance variables"""
        self.title_label: Optional[QLabel] = None
        self.subtitle_label: Optional[QLabel] = None
        self.status_icon: Optional[QLabel] = None
        self.new_measure_btn: Optional[QPushButton] = None
        self.additional_buttons: List[QPushButton] = []
        self._actions_layout: Optional[QHBoxLayout] = None

    def setup_ui(self, title: str, subtitle: str, breadcrumbs: Optional[List[Tuple[str, Callable]]] = None):
        """Setup UI with optional breadcrumbs"""
        self._setup_widget_styles()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 15, 30, 15)
        main_layout.setSpacing(8)

        # Top row: title and actions
        top_row = QHBoxLayout()

        # Title section
        title_section = self._create_title_section(title, subtitle, breadcrumbs)
        top_row.addLayout(title_section, 1)  # Stretch

        # Action buttons section
        self._setup_action_buttons(top_row)

        main_layout.addLayout(top_row)

    def _setup_widget_styles(self):
        """Setup widget styles"""
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
        self.setStyleSheet(f"""
            HeaderWidget {{
                background: {Styles.BACKGROUND_MEDIUM};
                border-bottom: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)

    def _create_title_section(self, title: str, subtitle: str,
                              breadcrumbs: Optional[List[Tuple[str, Callable]]]) -> QVBoxLayout:
        """Create title section with breadcrumbs, title and subtitle"""
        title_section = QVBoxLayout()
        title_section.setSpacing(2)

        # Add breadcrumbs if provided
        if breadcrumbs:
            self._setup_breadcrumbs(title_section, breadcrumbs)

        # Create title row with optional status icon
        title_row = self._create_title_row(title)
        title_section.addLayout(title_row)

        # ФИКС: Добавляем subtitle только если он не пустой и не содержит "исследование"
        if subtitle and "исследование" not in subtitle.lower():
            self.subtitle_label = self._create_subtitle_label(subtitle)
            title_section.addWidget(self.subtitle_label)

        return title_section

    def _create_title_row(self, title: str) -> QHBoxLayout:
        """Create title row with status icon and main title"""
        title_row = QHBoxLayout()

        # Status icon (hidden by default)
        self.status_icon = QLabel()
        self.status_icon.setStyleSheet(f"""
            QLabel {{
                color: {Styles.PRIMARY_LIGHT};
                font-size: 12px;
                margin-right: 8px;
            }}
        """)
        self.status_icon.hide()

        # Main title
        self.title_label = WidgetFactory.create_title(title, level=1)

        title_row.addWidget(self.status_icon)
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        return title_row

    def _create_subtitle_label(self, subtitle: str) -> QLabel:
        """Create subtitle label"""
        return WidgetFactory.create_label(
            subtitle,
            color=Styles.TEXT_SECONDARY,
            font_size=14
        )

    def _setup_breadcrumbs(self, parent_layout: QVBoxLayout,
                           breadcrumbs: List[Tuple[str, Callable]]) -> None:
        """Setup breadcrumb navigation"""
        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setSpacing(6)

        for i, (text, callback) in enumerate(breadcrumbs):
            # Add separator between breadcrumbs (except first)
            if i > 0:
                self._add_breadcrumb_separator(breadcrumb_layout)

            # Create breadcrumb button
            self._create_breadcrumb_button(breadcrumb_layout, text, callback)

        breadcrumb_layout.addStretch()
        parent_layout.addLayout(breadcrumb_layout)

    def _add_breadcrumb_separator(self, layout: QHBoxLayout) -> None:
        """Add separator between breadcrumbs"""
        sep = QLabel("›")
        sep.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 12px;")
        sep.setFixedWidth(10)
        layout.addWidget(sep)

    def _create_breadcrumb_button(self, layout: QHBoxLayout, text: str,
                                  callback: Optional[Callable]) -> QPushButton:
        """Create a breadcrumb button"""
        breadcrumb = QPushButton(text)
        breadcrumb.setStyleSheet(f"""
            QPushButton {{
                color: {Styles.TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 13px;
                padding: 0;
                font-weight: 400;
            }}
            QPushButton:hover {{
                color: {Styles.PRIMARY_LIGHT};
                text-decoration: underline;
            }}
        """)
        breadcrumb.setCursor(Qt.CursorShape.PointingHandCursor)

        if callback:
            breadcrumb.clicked.connect(callback)

        layout.addWidget(breadcrumb)
        return breadcrumb

    def _setup_action_buttons(self, parent_layout: QHBoxLayout) -> None:
        """Setup action buttons section"""
        self._actions_layout = QHBoxLayout()
        self._actions_layout.setSpacing(10)

        # Main action button
        self.new_measure_btn = self._create_main_action_button()
        self._actions_layout.addWidget(self.new_measure_btn)

        parent_layout.addLayout(self._actions_layout)

    def _create_main_action_button(self) -> QPushButton:
        """Create the main action button with fallback"""
        try:
            btn = AnimatedButton(self.MAIN_ACTION_TEXT)
        except (ImportError, AttributeError):
            btn = QPushButton(self.MAIN_ACTION_TEXT)

        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6A6BE1, stop:1 #8A8BEF);
            }
        """)

        return btn

    def add_action_button(self, text: str, callback: Optional[Callable] = None,
                          style: str = "secondary", icon: Optional[str] = None) -> QPushButton:
        """Add custom action button to header"""
        btn_text = f"{icon} {text}" if icon else text
        btn = QPushButton(btn_text)

        # Apply style
        if style == "primary":
            btn.setStyleSheet(self.ACTION_BUTTON_STYLES['primary'])
        else:
            formatted_style = self.ACTION_BUTTON_STYLES['secondary'].format(
                text_color=Styles.TEXT_PRIMARY,
                border_color=Styles.BORDER_MEDIUM
            )
            btn.setStyleSheet(formatted_style)

        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if callback:
            btn.clicked.connect(callback)

        # Add button to actions layout (before the main button)
        if self._actions_layout and self.new_measure_btn:
            self._actions_layout.insertWidget(self._actions_layout.count() - 1, btn)
            self.additional_buttons.append(btn)

        return btn

    def update_title(self, title: str, subtitle: Optional[str] = None) -> None:
        """Update header title and subtitle"""
        if self.title_label:
            self.title_label.setText(title)

        if subtitle is not None:
            # ФИКС: Не показываем подзаголовок если он содержит слово "исследование"
            if "исследование" in subtitle.lower():
                if self.subtitle_label:
                    self.subtitle_label.hide()
                return

            if self.subtitle_label:
                self.subtitle_label.setText(subtitle)
                self.subtitle_label.show()
            else:
                self._add_subtitle_label(subtitle)
        elif self.subtitle_label:
            self.subtitle_label.hide()

    def _add_subtitle_label(self, subtitle: str) -> None:
        """Add subtitle label if it doesn't exist"""
        self.subtitle_label = self._create_subtitle_label(subtitle)

        # Find title section and add subtitle
        title_section = self.title_label.parent().layout()
        if title_section:
            title_section.addWidget(self.subtitle_label)

    def set_status(self, status: str, icon: Optional[str] = None) -> None:
        """Set status with icon"""
        icon = icon or self.STATUS_ICONS.get(status, '')

        if icon and self.status_icon:
            self.status_icon.setText(icon)
            self.status_icon.show()
        elif self.status_icon:
            self.status_icon.hide()

    def set_action_visible(self, action_name: str, visible: bool) -> None:
        """Show/hide specific action button"""
        if action_name == 'new_measure' and self.new_measure_btn:
            self.new_measure_btn.setVisible(visible)
        # Можно добавить обработку дополнительных кнопок

    def clear_additional_buttons(self) -> None:
        """Remove all additional action buttons"""
        for btn in self.additional_buttons:
            if btn.parent():
                btn.setParent(None)
                btn.deleteLater()
        self.additional_buttons.clear()

    def set_main_action_text(self, text: str) -> None:
        """Update main action button text"""
        if self.new_measure_btn:
            self.new_measure_btn.setText(text)
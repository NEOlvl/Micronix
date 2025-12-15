"""
Reports page - optimized version
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QGridLayout
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import HeaderWidget
from styles import Styles


class ReportsPage(BasePage):
    """Reports page - optimized"""

    def __init__(self, parent=None):
        super().__init__("", "", parent)

        # Clear default layout
        self.clear_layout()

        # Setup UI
        self.setup_custom_header()
        self.setup_search_bar()
        self.setup_reports_grid()

    def clear_layout(self):
        """Clear the default layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_custom_header(self):
        """Setup custom header"""
        self.header = HeaderWidget("Отчёты", "", self)
        self.layout.addWidget(self.header)

    def setup_search_bar(self):
        """Setup search and actions bar"""
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        # Search input
        search_input = WidgetFactory.create_input("Поиск по названиям")
        search_input.setMinimumWidth(300)

        # Action buttons
        create_btn = WidgetFactory.create_button("Создать отчёт", style="primary")
        sort_btn = WidgetFactory.create_button("Сортировка", style="secondary")
        filter_btn = WidgetFactory.create_button("Фильтр", style="secondary")

        # Add widgets
        search_layout.addWidget(search_input)
        search_layout.addStretch()
        search_layout.addWidget(create_btn)
        search_layout.addWidget(sort_btn)
        search_layout.addWidget(filter_btn)

        self.layout.addLayout(search_layout)

    def setup_reports_grid(self):
        """Setup reports grid"""
        # Section title
        reports_label = WidgetFactory.create_title("Доступные отчёты", level=2)
        self.layout.addWidget(reports_label)

        # Create grid
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(16)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Sample reports data
        reports = [
            ("Отчёт #СВЧФ_1_01122024", "20.11.2024"),
            ("Отчёт #СВЧФ_3_01122024", "20.11.2024"),
            ("Отчёт #СО_1_01122024", "20.11.2024"),
            ("Отчёт #СВЧФ_3_01122024", "20.11.2024")
        ]

        # Add report cards to grid
        for i, (title, date) in enumerate(reports):
            row = i // 2
            col = i % 2
            report_card = self.create_report_card(title, date)
            grid_layout.addWidget(report_card, row, col)

        # Add grid to layout
        self.layout.addWidget(grid_widget, 1)

    def create_report_card(self, title, date):
        """Create a report card"""
        from widgets import ModernCard

        card = ModernCard()
        card.setFixedHeight(120)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(16)

        # Report icon
        icon = WidgetFactory.create_label("📄", font_size=32, align="center")
        icon.setFixedSize(60, 60)

        # Report info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # Title
        title_label = WidgetFactory.create_label(
            title,
            font_size=16,
            bold=True
        )

        # Date
        date_label = WidgetFactory.create_label(
            date,
            color=Styles.TEXT_SECONDARY,
            font_size=13
        )

        info_layout.addWidget(title_label)
        info_layout.addWidget(date_label)
        info_layout.addStretch()

        card_layout.addWidget(icon)
        card_layout.addLayout(info_layout, 1)

        # Make card clickable
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        return card
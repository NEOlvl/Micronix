"""
Base class for all pages
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from widget_factory import WidgetFactory


class BasePage(QWidget):
    """Base class for all application pages"""

    def __init__(self, title="", subtitle="", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.layout = None
        self.setup_ui()

    def setup_ui(self):
        """Setup basic page layout"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(20)

        if self.title:
            self.add_header()

    def add_header(self, title=None, subtitle=None):
        """Add page header"""
        title = title or self.title
        subtitle = subtitle or self.subtitle

        # Add title
        title_label = WidgetFactory.create_title(title, level=1)
        self.layout.addWidget(title_label)

        # Add subtitle if exists
        if subtitle:
            subtitle_label = WidgetFactory.create_label(
                subtitle,
                color="rgba(255, 255, 255, 0.6)",
                font_size=14
            )
            self.layout.addWidget(subtitle_label)

        # Add some spacing
        self.layout.addSpacing(10)

    def add_card(self, content, title=None, layout_type="vertical"):
        """Add a card with content"""
        from widgets import ModernCard

        # Create card
        card = ModernCard()

        # Create layout for card
        if layout_type == "vertical":
            card_layout = QVBoxLayout(card)
        else:
            card_layout = QHBoxLayout(card)

        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        # Add title if provided
        if title:
            title_label = WidgetFactory.create_title(title, level=2)
            card_layout.addWidget(title_label)

        # Add content
        if isinstance(content, list):
            for widget in content:
                card_layout.addWidget(widget)
        else:
            card_layout.addWidget(content)

        # Add card to page
        self.layout.addWidget(card)

        return card

    def add_section(self, title, content=None):
        """Add a section with title"""
        # Add section title
        section_title = WidgetFactory.create_title(title, level=2)
        self.layout.addWidget(section_title)

        # Add content if provided
        if content:
            if isinstance(content, list):
                for widget in content:
                    self.layout.addWidget(widget)
            else:
                self.layout.addWidget(content)

        return section_title
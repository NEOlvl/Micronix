"""
Widget factory for creating common UI components
"""

from PyQt6.QtWidgets import (QLabel, QPushButton, QLineEdit, QVBoxLayout,
                             QHBoxLayout, QFrame, QScrollArea, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt
from styles import Styles


class WidgetFactory:
    """Factory for creating styled widgets"""

    @staticmethod
    def create_label(text, font_size=14, color=None, bold=False, align=None):
        label = QLabel(text)

        # Build style string
        style_parts = []
        style_parts.append(f"color: {color or Styles.TEXT_PRIMARY}")
        style_parts.append(f"font-size: {font_size}px")

        if bold:
            style_parts.append("font-weight: 600")

        style_parts.append("background: transparent")

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
        sizes = {1: 24, 2: 18, 3: 16}
        colors = {1: Styles.TEXT_PRIMARY, 2: Styles.TEXT_PRIMARY, 3: Styles.TEXT_SECONDARY}

        return WidgetFactory.create_label(
            text=text,
            font_size=sizes.get(level, 16),
            color=colors.get(level, Styles.TEXT_PRIMARY),
            bold=True
        )

    @staticmethod
    def create_button(text, style="primary", icon=None, size=None):
        btn = QPushButton(text)

        if icon:
            btn.setIcon(icon)

        # Apply style
        if style == "primary":
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Styles.PRIMARY}, stop:1 {Styles.PRIMARY_LIGHT});
                    color: {Styles.TEXT_PRIMARY};
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
            """)
        elif style == "secondary":
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.1);
                    color: {Styles.TEXT_PRIMARY};
                    border: 1px solid {Styles.BORDER_MEDIUM};
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.15);
                }}
            """)
        elif style == "danger":
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: white;
                    background: rgba(239, 68, 68, 0.2);
                    border: 1px solid rgba(239, 68, 68, 0.4);
                    padding: 8px 16px;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: rgba(239, 68, 68, 0.3);
                }}
            """)

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
        input_field.setStyleSheet(style or f"""
            QLineEdit {{
                background: rgba(40, 41, 44, 0.9);
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 6px;
                padding: 8px 12px;
                color: {Styles.TEXT_PRIMARY};
                selection-background-color: rgba(120, 121, 241, 0.5);
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(120, 121, 241, 0.6);
            }}
        """)
        return input_field

    @staticmethod
    def create_combo(items=None):
        combo = QComboBox()
        if items:
            combo.addItems(items)
        combo.setStyleSheet(f"""
            QComboBox {{
                background: rgba(40, 41, 44, 0.9);
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 6px;
                padding: 8px 12px;
                color: {Styles.TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border: 1px solid rgba(120, 121, 241, 0.6);
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        return combo

    @staticmethod
    def create_spinbox(min_val=0, max_val=100, default=0):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setStyleSheet(f"""
            QSpinBox {{
                background: rgba(40, 41, 44, 0.9);
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 6px;
                padding: 8px 12px;
                color: {Styles.TEXT_PRIMARY};
            }}
            QSpinBox:focus {{
                border: 1px solid rgba(120, 121, 241, 0.6);
            }}
        """)
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
        if vertical:
            divider.setFrameShape(QFrame.Shape.VLine)
            divider.setFixedWidth(1)
        else:
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setFixedHeight(1)

        divider.setStyleSheet(f"background: {Styles.BORDER_LIGHT};")
        return divider

    @staticmethod
    def create_scroll_area(widget=None):
        """Create a styled scroll area"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        if widget:
            scroll.setWidget(widget)

        return scroll
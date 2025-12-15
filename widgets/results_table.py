"""
Results table widget
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView


class ResultsTableWidget(QTableWidget):
    """Styled results table"""

    def __init__(self, parent=None):
        super().__init__(0, 5, parent)
        self.setup_ui()

    def setup_ui(self):
        headers = ["№", "Имя образца", "Тангенс угла потерь (tgδ)",
                   "Диэлектрическая проницаемость (ε)", "Относительная погрешность (δ)"]
        self.setHorizontalHeaderLabels(headers)

        # Style the table
        self.setStyleSheet("""
            QTableWidget {
                background: rgba(30, 31, 34, 0.9);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.1);
                font-size: 13px;
                alternate-background-color: rgba(255, 255, 255, 0.05);
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                background: transparent;
            }
            QTableWidget::item:selected {
                background: rgba(120, 121, 241, 0.3);
            }
            QHeaderView::section {
                background: rgba(40, 41, 44, 0.8);
                color: white;
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: 600;
            }
            QHeaderView::section:last {
                border-right: none;
            }
        """)

        # Включить чередование строк
        self.setAlternatingRowColors(True)

        # Configure header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
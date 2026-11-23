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

        # Стиль таблицы — из единой темы APP_QSS

        # Включить чередование строк
        self.setAlternatingRowColors(True)

        # Configure header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
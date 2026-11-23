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

    def __init__(self, main_window=None, parent=None):  # Добавляем параметр main_window
        super().__init__("", "", parent)
        self.main_window = main_window  # Сохраняем ссылку на главное окно

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

        # Используем сохраненную ссылку на главное окно
        if self.main_window and hasattr(self.main_window, 'open_new_measurement_page'):
            # Подключаем кнопку "Новое исследование" в хедере
            self.header.new_measure_btn.clicked.connect(
                lambda: self.main_window.open_new_measurement_page()
            )
        else:
            print("Предупреждение: Главное окно не передано в ReportsPage")

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

        # Create grid container (заполняется в load_reports)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # Add grid to layout
        self.layout.addWidget(self.grid_widget, 1)
        self.load_reports()

    def load_reports(self):
        """Загрузить карточки отчётов из БД измерений (ТЗ-9)."""
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        backend = getattr(self.main_window, 'backend', None)
        measurements = (backend.list_measurements()
                        if backend is not None else [])

        if not measurements:
            empty = WidgetFactory.create_label(
                "Нет сохранённых измерений",
                color=Styles.TEXT_SECONDARY, font_size=14)
            self.grid_layout.addWidget(empty, 0, 0)
            return

        for i, m in enumerate(measurements):
            row, col = divmod(i, 2)
            card = self.create_report_card(
                f"Отчёт #{m['title']}", str(m['created_at'])[:10],
                m['measure_id'])
            self.grid_layout.addWidget(card, row, col)

    def open_report(self, measure_id):
        """Сгенерировать PDF по измерению и открыть файл (ТЗ-8)."""
        import os
        backend = getattr(self.main_window, 'backend', None)
        if backend is None:
            return
        try:
            path = backend.generate_report(measure_id)
            os.startfile(path)
        except Exception as exc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Отчёт",
                f"Не удалось создать отчёт: {exc}")

    def create_report_card(self, title, date, measure_id=None):
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

        # Make card clickable — открывает сгенерированный PDF
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        if measure_id:
            card.mousePressEvent = (
                lambda e, mid=measure_id: self.open_report(mid))

        return card
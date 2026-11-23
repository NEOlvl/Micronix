"""
Measures page - optimized version
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel)
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import HeaderWidget
from styles import Styles


class MeasuresPage(BasePage):
    """Measurements list page - optimized"""

    def __init__(self, backend, open_measure_callback, parent=None):
        super().__init__("", "", parent)
        self.backend = backend
        self.open_measure_callback = open_measure_callback

        # Clear default layout
        self.clear_layout()

        # Setup UI
        self.setup_custom_header()
        self.setup_search_bar()
        self.setup_measurements_grid()

        # Load measurements
        self.load_measurements()

    def clear_layout(self):
        """Clear the default layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_custom_header(self):
        """Setup custom header"""
        self.header = HeaderWidget("Измерения", "", self)

        # Update button text and style
        self.header.new_measure_btn.setText("Новое исследование")

        self.layout.addWidget(self.header)

    def setup_search_bar(self):
        """Setup search and filter bar"""
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        # Search input
        search_input = WidgetFactory.create_input("Поиск по названиям")
        search_input.setMinimumWidth(300)
        search_input.textChanged.connect(self.filter_measurements)

        # Action buttons
        create_btn = WidgetFactory.create_button("Создать измерение", style="primary")
        create_btn.clicked.connect(self.create_measurement)

        sort_btn = WidgetFactory.create_button("Сортировка", style="secondary")
        filter_btn = WidgetFactory.create_button("Фильтр", style="secondary")

        # Add widgets to layout
        search_layout.addWidget(search_input)
        search_layout.addStretch()
        search_layout.addWidget(create_btn)
        search_layout.addWidget(sort_btn)
        search_layout.addWidget(filter_btn)

        self.layout.addLayout(search_layout)

    def setup_measurements_grid(self):
        """Setup measurements grid with scroll area"""
        self.measures_scroll = WidgetFactory.create_scroll_area()
        self.measures_widget = QWidget()
        self.measures_layout = QVBoxLayout(self.measures_widget)
        self.measures_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.measures_scroll.setWidget(self.measures_widget)

        self.layout.addWidget(self.measures_scroll, 1)

    def load_measurements(self):
        """Load and display all measurements in 2-column grid"""
        # Clear existing content
        for i in reversed(range(self.measures_layout.count())):
            item = self.measures_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Get measurements from backend
        measures = self.backend.query("measure_data", 0)

        if not measures:
            self.show_empty_state()
            return

        # Создаем сетку для всех измерений
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 20)

        # Добавляем все измерения в сетку 2 колонки
        for i, measure in enumerate(measures):
            row = i // 2
            col = i % 2
            measure_card = self.create_measurement_card(measure)
            grid_layout.addWidget(measure_card, row, col)

        # Добавляем сетку в скролл
        self.measures_layout.addWidget(grid_widget)

    def show_empty_state(self):
        """Show empty state when no measurements"""
        empty_label = WidgetFactory.create_label(
            "Нет проведенных измерений",
            color="rgba(255, 255, 255, 0.5)",
            align="center"
        )
        empty_label.setFixedHeight(200)
        self.measures_layout.addWidget(empty_label)

    def create_measurement_card(self, measure):
        """Create a measurement card for the list view - обновленный дизайн"""
        from widgets import ModernCard
        from PyQt6.QtWidgets import QFrame

        card = ModernCard()
        card.setFixedHeight(160)  # Чуть больше для страницы измерений
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(15)

        # ЛЕВАЯ ЧАСТЬ: График
        graph_container = QFrame()
        graph_container.setFixedSize(180, 120)
        graph_container.setStyleSheet(f"""
            QFrame {{
                background: {Styles.BACKGROUND_DARK};
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)

        # Заглушка графика
        graph_label = QLabel("📈")
        graph_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: rgba(255, 255, 255, 0.5);
                background: transparent;
            }
        """)
        graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        graph_layout = QVBoxLayout(graph_container)
        graph_layout.addWidget(graph_label)

        card_layout.addWidget(graph_container)

        # ПРАВАЯ ЧАСТЬ: Детальная информация
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок — имя метода из реестра backend
        try:
            method_names = {m['id']: m['name']
                            for m in self.backend.list_methods()}
        except AttributeError:
            method_names = {}

        method_id = measure.get('method_id')
        method_title = method_names.get(method_id, f"Метод {method_id}")

        title = WidgetFactory.create_label(
            method_title,
            font_size=16,
            bold=True
        )
        title.setStyleSheet("color: white;")

        # ID и время
        measure_id_label = WidgetFactory.create_label(
            f"#{measure['title']} • {measure['time']}",
            color=Styles.TEXT_SECONDARY,
            font_size=13
        )

        # Результаты образцов
        if measure.get('y_samples'):
            for sample_idx, sample in measure['y_samples'].items():
                sample_name = sample.get('name', f"Образец {sample_idx}")
                result_text = (f"{sample_name}: "
                               f"tg\u03b4={sample.get('tgo') or 0:.2e}, "
                               f"\u03b5={sample.get('E') or 0:.2f}")
                result_label = WidgetFactory.create_label(
                    result_text,
                    color="rgba(255, 255, 255, 0.8)",
                    font_size=13
                )
                info_layout.addWidget(result_label)

        # Добавляем элементы
        info_layout.addWidget(title)
        info_layout.addWidget(measure_id_label)
        info_layout.addStretch()

        card_layout.addLayout(info_layout, 1)

        # Кликабельность
        card.mousePressEvent = lambda event, mid=measure['id_m']: self.open_measurement(mid, event)

        return card

    def open_measurement(self, measure_id, event):
        """Open measurement details"""
        self.open_measure_callback(measure_id)

    def create_measurement(self):
        """Create new measurement"""
        main_window = self.parent().parent()
        if hasattr(main_window, 'show_method_panel'):
            main_window.show_method_panel(1)
        self.load_measurements()

    def filter_measurements(self, text):
        """Filter measurements based on search text"""
        # Implementation would filter the displayed measurements
        print(f"Filtering by: {text}")
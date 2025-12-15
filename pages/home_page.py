"""
Home page with purple header
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QGridLayout
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import HeaderWidget, MethodCard


class HomePage(BasePage):
    """Main home page with purple header"""

    def __init__(self, backend, open_measure_callback, parent=None):
        super().__init__("", "", parent)  # Empty title, we'll use custom header
        self.backend = backend
        self.open_measure_callback = open_measure_callback
        self.method_cards = []  # Для хранения ссылок на карточки методов

        # Clear default layout
        self.clear_layout()

        # Setup custom UI with header
        self.setup_custom_header()
        self.setup_methods_section()  # Убираем setup_welcome_section
        self.setup_recent_measurements()

    def clear_layout(self):
        """Clear the default layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_custom_header(self):
        """Setup custom purple header"""
        self.header = HeaderWidget("Главная", "Добро пожаловать в FERRO", self)

        # Делаем header полностью фиолетовым
        self.header.setStyleSheet(f"""
            HeaderWidget {{
                background: #7879F1;
                border-bottom: none;
            }}

            QLabel {{
                color: white !important;
            }}

            QPushButton {{
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }}
        """)

        # Прячем кнопку "Новое исследование" в header - она есть в сайдбаре
        self.header.new_measure_btn.hide()

        self.layout.addWidget(self.header)

    def setup_methods_section(self):
        """Setup method selection section - сразу после header"""
        # Убираем заголовок "Выберите метод исследования:" - начинаем сразу с карточек

        # Method cards grid
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(0, 30, 0, 30)  # Отступы сверху и снизу

        # 6 методов согласно изображению
        methods = [
            {
                "id": 1,
                "name": "Метод 1",
                "title": "Метод объёмного резонатора при фиксированной резонансной частоте",
                "icon": "📡",
                "color": "#7879F1"
            },
            {
                "id": 2,
                "name": "Метод 2",
                "title": "Метод объёмного резонатора при фиксированной резонансной длине",
                "icon": "📏",
                "color": "#9A9BFF"
            },
            {
                "id": 3,
                "name": "Метод 3",
                "title": "Метод объёмного резонатора для стержневых образцов",
                "icon": "🔩",
                "color": "#f8c33c"
            },
            {
                "id": 4,
                "name": "Метод 4",
                "title": "Метод объёмного резонатора для СВЧ ферритов",
                "icon": "🌀",
                "color": "#6A6BE1"
            },
            {
                "id": 5,
                "name": "Метод 5",
                "title": "Метод измерений диэлектрических параметров",
                "icon": "⚡",
                "color": "#9D7BF1"
            },
            {
                "id": 6,
                "name": "Метод 6",
                "title": "Расширенный метод анализа материалов",
                "icon": "🔬",
                "color": "#B19BFF"
            }
        ]

        self.method_cards.clear()
        for i, method_data in enumerate(methods):
            row = i // 3  # 3 карточки в ряд
            col = i % 3

            card = MethodCard(
                method_num=method_data["id"],
                method_name=method_data["name"],
                method_title=method_data["title"],
                icon=method_data["icon"],
                color=method_data["color"]
            )

            # Подключаем сигнал
            card.clicked.connect(lambda checked, mid=method_data["id"]: self.open_measurement_page(mid))

            grid_layout.addWidget(card, row, col)
            self.method_cards.append(card)

        self.layout.addWidget(grid_widget)

    def open_measurement_page(self, method_id):
        """Open measurement page with selected method"""
        main_window = self.parent().parent()
        if hasattr(main_window, 'open_new_measurement_page'):
            main_window.open_new_measurement_page(method_id)

    def setup_recent_measurements(self):
        """Setup recent measurements section"""
        # Создаем контейнер с легким фоном для разделения
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: rgba(0, 0, 0, 0.1);")
        self.layout.addWidget(separator)

        # Create section header with "View all" button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 30, 0, 20)

        recent_label = WidgetFactory.create_title("Последние исследования", level=2)
        recent_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 20px;
                font-weight: 600;
                background: transparent;
                margin-bottom: 15px;
            }
        """)
        header_layout.addWidget(recent_label)
        header_layout.addStretch()

        all_measures_btn = WidgetFactory.create_button(
            "все исследования >",
            style="secondary"
        )
        all_measures_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #7879F1;
                border: none;
                font-size: 14px;
                padding: 0;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #6A6BE1;
                text-decoration: underline;
            }
        """)
        all_measures_btn.clicked.connect(self.show_all_measurements)
        header_layout.addWidget(all_measures_btn)

        self.layout.addLayout(header_layout)

        # Create scroll area for recent measurements
        self.recent_scroll = WidgetFactory.create_scroll_area()
        self.recent_widget = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_widget)
        self.recent_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.recent_layout.setSpacing(15)
        self.recent_scroll.setWidget(self.recent_widget)

        self.layout.addWidget(self.recent_scroll, 1)

        # Load measurements
        self.load_recent_measurements()

    def show_all_measurements(self):
        """Navigate to measurements page"""
        main_window = self.parent().parent()
        if main_window:
            # Находим кнопку "Измерения" в sidebar
            for btn in main_window.sidebar.nav_buttons:
                if "Измерения" in btn.text():
                    btn.click()
                    break

    def load_recent_measurements(self):
        """Load and display recent measurements"""
        # Clear existing content
        for i in reversed(range(self.recent_layout.count())):
            item = self.recent_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Get measurements from backend
        measures = self.backend.ferro_query("measure_data", 0)

        if not measures:
            # Show empty state
            empty_widget = QWidget()
            empty_widget.setStyleSheet("background: transparent;")
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_icon = WidgetFactory.create_label(
                "📊",
                font_size=48,
                align="center"
            )
            empty_icon.setStyleSheet("color: #CCCCCC;")

            empty_text = WidgetFactory.create_label(
                "Пока нет проведенных исследований",
                color="#999999",
                align="center",
                font_size=16
            )

            empty_layout.addWidget(empty_icon)
            empty_layout.addWidget(empty_text)
            empty_widget.setFixedHeight(150)

            self.recent_layout.addWidget(empty_widget)
            return

        # Show last 3 measurements
        for measure in measures[-3:]:
            measure_card = self.create_measurement_card(measure)
            self.recent_layout.addWidget(measure_card)

    def create_measurement_card(self, measure):
        """Create a measurement card widget"""
        from widgets import ModernCard

        card = ModernCard()
        card.setFixedHeight(100)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            ModernCard {
                background: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
            }
            ModernCard:hover {
                background: #F8F9FA;
                border: 1px solid #7879F1;
            }
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # Method icon based on method type
        method_icons = {
            1: "📡", 2: "📏", 3: "🔩", 4: "🌀", 5: "⚡", 6: "🔬"
        }

        method_id = measure.get('method_id', 1)
        method_icon = method_icons.get(method_id, "📊")

        icon_widget = WidgetFactory.create_label(
            method_icon,
            font_size=28,
            align="center"
        )
        icon_widget.setFixedSize(60, 60)
        icon_widget.setStyleSheet("""
            background: #7879F1; 
            color: white;
            border-radius: 10px;
        """)

        card_layout.addWidget(icon_widget)

        # Measurement info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Title
        title = WidgetFactory.create_label(
            f"Исследование #{measure.get('title', 'Unknown')}",
            font_size=16,
            bold=True
        )
        title.setStyleSheet("color: #333333;")

        # Time and method
        method_names = {
            1: "ФРЧ", 2: "ФРД", 3: "СО", 4: "СВЧФ", 5: "Метод 5", 6: "Метод 6"
        }

        method_name = method_names.get(method_id, f"Метод {method_id}")
        time_str = measure.get('time', 'Неизвестно')

        details_label = WidgetFactory.create_label(
            f"{method_name} • {time_str}",
            color="#666666",
            font_size=13
        )

        # Sample info if available
        sample_info = WidgetFactory.create_label("")
        if measure.get('y_samples'):
            sample = list(measure['y_samples'].values())[0]
            sample_info.setText(f"Образец: {sample.get('name', 'Неизвестно')}")
            sample_info.setStyleSheet("color: #666666; font-size: 13px;")

        info_layout.addWidget(title)
        info_layout.addWidget(details_label)
        info_layout.addWidget(sample_info)
        info_layout.addStretch()

        card_layout.addLayout(info_layout, 1)

        # Connect click
        card.mousePressEvent = lambda event, mid=measure['id_m']: self.open_measurement(mid, event)

        return card

    def open_measurement(self, measure_id, event):
        """Open measurement details"""
        self.open_measure_callback(measure_id)

    def refresh_page(self):
        """Refresh page content"""
        self.load_recent_measurements()
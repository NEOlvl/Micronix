"""
Home page with purple header - UPDATED VERSION with categories and scrollable layout
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QGridLayout, QMainWindow, QPushButton, QScrollArea
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import HeaderWidget, MethodCard
from styles import Styles


class HomePage(BasePage):
    """Main home page with purple header - теперь полностью прокручиваемая"""

    def __init__(self, backend, open_measure_callback, parent=None):
        super().__init__("", "", parent)  # Empty title, we'll use custom header
        self.backend = backend
        self.open_measure_callback = open_measure_callback
        self.method_cards = []  # Для хранения ссылок на карточки методов

        # Clear default layout
        self.clear_layout()

        # Setup custom UI with header and scrollable content
        self.setup_custom_header()
        self.setup_scrollable_content()

    def clear_layout(self):
        """Clear the default layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_custom_header(self):
        """Setup custom purple header - ОСТАВЛЯЕМ БЕЗ ИЗМЕНЕНИЙ"""
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

    def setup_scrollable_content(self):
        """Setup scrollable content area"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # Create content widget
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(30, 20, 30, 20)
        self.content_layout.setSpacing(30)  # Увеличиваем spacing между секциями

        # Add all sections
        self.setup_methods_section()
        self.setup_recent_measurements()  # Этот метод нужно добавить
        self.setup_recent_reports()  # Добавляем секцию с отчетами

        # Add spacer at the end
        self.content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        self.layout.addWidget(scroll_area, 1)

    def setup_methods_section(self):
        """Setup method selection section - обновляем с упрощенными карточками"""
        # Section title
        section_title = WidgetFactory.create_label("Выберите метод исследования:", font_size=18, bold=True)
        section_title.setStyleSheet("color: white; margin-bottom: 20px;")
        self.content_layout.addWidget(section_title)

        # Method cards grid - теперь 3 карточки в ряд (упрощенные)
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 20)

        # 6 методов с категориями: 1,2,3,5 - Диэлектрики, 4,6 - Ферриты
        methods = [
            {
                "id": 1,
                "name": "Метод фиксированной частоты",
                "title": "Измерение диэлектрических параметров материалов методом объёмного резонатора при фиксированной резонансной частоте",
                "category": "Диэлектрики",
                "color": "#7879F1"
            },
            {
                "id": 2,
                "name": "Метод фиксированной длины",
                "title": "Измерение диэлектрических параметров материалов методом объёмного резонатора при фиксированной резонансной длине",
                "category": "Диэлектрики",
                "color": "#9A9BFF"
            },
            {
                "id": 3,
                "name": "Метод для стержневых образцов",
                "title": "Измерение диэлектрических параметров стержневых образцов методом объёмного резонатора",
                "category": "Диэлектрики",
                "color": "#f8c33c"
            },
            {
                "id": 4,
                "name": "Метод для СВЧ ферритов",
                "title": "Измерение диэлектрических параметров СВЧ ферритов методом объёмного резонатора",
                "category": "Ферриты",
                "color": "#FF6B6B"
            },
            {
                "id": 5,
                "name": "Метод измерения диэлектрических параметров",
                "title": "Современный метод измерений диэлектрических параметров различных материалов",
                "category": "Диэлектрики",
                "color": "#9D7BF1"
            },
            {
                "id": 6,
                "name": "Расширенный метод анализа",
                "title": "Расширенный метод анализа материалов с повышенной точностью измерений",
                "category": "Ферриты",
                "color": "#FF8E53"
            }
        ]

        self.method_cards.clear()
        for i, method_data in enumerate(methods):
            row = i // 3  # Теперь 3 карточки в ряд
            col = i % 3

            card = MethodCard(
                method_num=method_data["id"],
                method_name=method_data["name"],
                method_title=method_data["title"],
                category=method_data["category"],
                color=method_data["color"]
            )

            # Высота для карточек
            card.setFixedHeight(160)
            card.setMinimumWidth(350)

            # ПРАВИЛЬНОЕ подключение сигнала
            card.clicked.connect(lambda mid=method_data["id"]: self.open_measurement_page(mid))

            grid_layout.addWidget(card, row, col, 1, 1, Qt.AlignmentFlag.AlignTop)
            self.method_cards.append(card)

        self.content_layout.addWidget(grid_widget)

    def setup_recent_measurements(self):
        """Setup recent measurements section"""
        # Создаем контейнер с легким фоном для разделения
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: rgba(0, 0, 0, 0.1);")
        self.content_layout.addWidget(separator)

        # Create section header with "View all" button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 30, 0, 20)

        recent_label = WidgetFactory.create_title("Последние исследования", level=2)
        recent_label.setStyleSheet("""
            QLabel {
                color: white;
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

        self.content_layout.addLayout(header_layout)

        # Create scroll area for recent measurements
        self.recent_scroll = WidgetFactory.create_scroll_area()
        self.recent_widget = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_widget)
        self.recent_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.recent_layout.setSpacing(15)
        self.recent_scroll.setWidget(self.recent_widget)

        self.content_layout.addWidget(self.recent_scroll)

        # Load measurements
        self.load_recent_measurements()

    def setup_recent_reports(self):
        """Setup recent reports section"""
        # Section header with "View all" button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 20)

        reports_label = WidgetFactory.create_title("Последние отчёты", level=2)
        reports_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 600;
                background: transparent;
            }
        """)
        header_layout.addWidget(reports_label)
        header_layout.addStretch()

        all_reports_btn = WidgetFactory.create_button(
            "все отчёты >",
            style="secondary"
        )
        all_reports_btn.setStyleSheet("""
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
        all_reports_btn.clicked.connect(self.show_all_reports)
        header_layout.addWidget(all_reports_btn)

        self.content_layout.addLayout(header_layout)

        # Reports grid
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Sample reports data - в реальном приложении здесь будут данные из бэкенда
        reports = [
            ("Отчёт #СВЧФ_1_01122024", "20.11.2024", "СВЧФ", "#FF6B6B"),
            ("Отчёт #СВЧФ_3_01122024", "20.11.2024", "СВЧФ", "#FF6B6B"),
            ("Отчёт #СО_1_01122024", "19.11.2024", "СО", "#f8c33c"),
            ("Отчёт #ФРЧ_2_01122024", "18.11.2024", "ФРЧ", "#7879F1")
        ]

        for i, (title, date, method_type, color) in enumerate(reports):
            row = i // 2
            col = i % 2
            report_card = self.create_report_card(title, date, method_type, color)
            grid_layout.addWidget(report_card, row, col)

        self.content_layout.addWidget(grid_widget)

    # ОСТАЛЬНЫЕ МЕТОДЫ - КОПИРУЕМ ИЗ ПРЕДЫДУЩЕЙ ВЕРСИИ
    def open_measurement_page(self, method_id):
        """Open measurement page with selected method"""
        print(f"Opening measurement page for method {method_id}")

        # Получаем главное окно
        main_window = self.parent()
        while main_window and not isinstance(main_window, QMainWindow):
            main_window = main_window.parent()

        if main_window and hasattr(main_window, 'open_new_measurement_page'):
            print(f"Found main window, calling open_new_measurement_page({method_id})")
            main_window.open_new_measurement_page(method_id)
        else:
            print("Main window not found or doesn't have required method")
            # Альтернативный способ
            self.navigate_to_new_measurement(method_id)

    def navigate_to_new_measurement(self, method_id):
        """Alternative navigation to new measurement page"""
        print(f"Alternative navigation for method {method_id}")

        # Получаем доступ к главному окну через цепочку родителей
        widget = self
        main_window = None

        # Ищем главное окно
        while widget:
            if hasattr(widget, 'page_stack'):
                main_window = widget
                break
            widget = widget.parent()

        if main_window and hasattr(main_window, 'page_stack'):
            # Перебираем все виджеты в stack
            for i in range(main_window.page_stack.count()):
                widget = main_window.page_stack.widget(i)
                if widget.__class__.__name__ == "NewMeasurementPage":
                    # Устанавливаем выбранный метод
                    if hasattr(widget, 'selected_method'):
                        widget.selected_method = method_id
                    if hasattr(widget, 'refresh_parameters'):
                        widget.refresh_parameters()

                    # Переключаемся на страницу
                    main_window.page_stack.setCurrentWidget(widget)

                    # Активируем кнопку в сайдбаре если возможно
                    if hasattr(main_window, 'sidebar'):
                        # Ищем кнопку "Новое исследование"
                        for child in main_window.sidebar.findChildren(QPushButton):
                            if "Новое исследование" in child.text():
                                if hasattr(main_window.sidebar, 'set_active_button'):
                                    main_window.sidebar.set_active_button(child)
                                break
                    return

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
            empty_icon.setStyleSheet("color: rgba(255, 255, 255, 0.5);")

            empty_text = WidgetFactory.create_label(
                "Пока нет проведенных исследований",
                color="rgba(255, 255, 255, 0.5)",
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
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            ModernCard:hover {
                background: rgba(255, 255, 255, 0.08);
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
        icon_widget.setStyleSheet(f"""
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
        title.setStyleSheet("color: white;")

        # Time and method
        method_names = {
            1: "ФРЧ", 2: "ФРД", 3: "СО", 4: "СВЧФ", 5: "Метод 5", 6: "Метод 6"
        }

        method_name = method_names.get(method_id, f"Метод {method_id}")
        time_str = measure.get('time', 'Неизвестно')

        details_label = WidgetFactory.create_label(
            f"{method_name} • {time_str}",
            color="rgba(255, 255, 255, 0.7)",
            font_size=13
        )

        # Sample info if available
        sample_info = WidgetFactory.create_label("")
        if measure.get('y_samples'):
            sample = list(measure['y_samples'].values())[0]
            sample_info.setText(f"Образец: {sample.get('name', 'Неизвестно')}")
            sample_info.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 13px;")

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

    def create_report_card(self, title, date, method_type, color):
        """Create a report card widget"""
        from widgets import ModernCard

        card = ModernCard()
        card.setFixedHeight(100)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            ModernCard {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }}
            ModernCard:hover {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {color};
            }}
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # Report icon
        icon_widget = WidgetFactory.create_label("📄", font_size=24, align="center")
        icon_widget.setFixedSize(50, 50)
        icon_widget.setStyleSheet(f"""
            background: {color}; 
            color: white;
            border-radius: 8px;
        """)

        # Report info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Title
        report_title = WidgetFactory.create_label(
            title,
            font_size=14,
            bold=True
        )
        report_title.setStyleSheet("color: white;")

        # Method and date
        method_label = WidgetFactory.create_label(
            f"{method_type} • {date}",
            color="rgba(255, 255, 255, 0.7)",
            font_size=12
        )

        # Status
        status_label = WidgetFactory.create_label(
            "✓ Готов",
            color=color,
            font_size=11,
            bold=True
        )
        status_label.setStyleSheet(f"background: {color}20; padding: 2px 8px; border-radius: 4px;")

        info_layout.addWidget(report_title)
        info_layout.addWidget(method_label)
        info_layout.addWidget(status_label)
        info_layout.addStretch()

        card_layout.addWidget(icon_widget)
        card_layout.addLayout(info_layout, 1)

        # Connect click (в реальном приложении здесь будет открытие отчета)
        card.mousePressEvent = lambda event, t=title: self.open_report(t, event)

        return card

    def open_report(self, report_title, event):
        """Open report - в реальном приложении здесь будет переход на страницу отчета"""
        print(f"Opening report: {report_title}")
        # Можно добавить навигацию на страницу отчетов с предвыбранным отчетом

    def show_all_reports(self):
        """Navigate to reports page"""
        main_window = self.parent().parent()
        if main_window:
            # Находим кнопку "Отчёты" в sidebar
            for btn in main_window.sidebar.nav_buttons:
                if "Отчёты" in btn.text():
                    btn.click()
                    break

    def refresh_page(self):
        """Refresh page content"""
        self.load_recent_measurements()
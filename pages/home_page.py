"""
Home page with purple header - UPDATED VERSION with categories and scrollable layout
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QGridLayout, QMainWindow, QPushButton, QScrollArea, \
    QLabel
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import HeaderWidget, MethodCard


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

    def create_section_title(self, text, font_size=20):
        """Создание заголовка секции с единым стилем"""
        return WidgetFactory.create_label(text, role="h2")

    def clear_layout(self):
        """Clear the default layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_custom_header(self):
        """Setup custom purple header - ПРАВИЛЬНОЕ ПРОДОЛЖЕНИЕ САЙДБАРА"""
        # Создаем пустой header без текста
        self.header = QWidget()

        # Высота должна быть такой же как header сайдбара - 100px
        self.header.setFixedHeight(100)

        # Убираем все отступы у header
        self.header.setContentsMargins(0, 0, 0, 0)

        # Фиолетовая шапка — продолжение сайдбара, единый стиль
        # из темы (#accentHeader). Внутри — название страницы.
        self.header.setObjectName("accentHeader")
        self.header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(30, 0, 30, 0)
        page_title = QLabel("Главная")
        page_title.setProperty("role", "accentTitle")
        header_layout.addWidget(page_title)
        header_layout.addStretch()

        # Добавляем в layout без отступов
        self.layout.addWidget(self.header)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы у основного layout

    def setup_scrollable_content(self):
        """Setup scrollable content area"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create content widget
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(30, 20, 30, 20)  # Восстанавливаем отступы только для контента
        self.content_layout.setSpacing(20)

        # Add all sections
        self.setup_methods_section()
        self.setup_recent_measurements()
        self.setup_recent_reports()

        # Add spacer at the end
        self.content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        self.layout.addWidget(scroll_area, 1)

    def setup_methods_section(self):
        """Setup method selection section - обновляем с упрощенными карточками"""

        # Method cards grid - теперь 3 карточки в ряд (упрощенные)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 20)

        # Устанавливаем одинаковые пропорции колонок
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)

        # Карточки методов — из реестра backend (ТЗ-9, ТЗ-3)
        palette = ["#7879F1", "#9A9BFF", "#f8c33c", "#FF6B6B",
                   "#9D7BF1", "#FF8E53"]
        try:
            methods = self.backend.list_methods()
        except AttributeError:
            methods = []

        self.method_cards.clear()
        for i, method_data in enumerate(methods):
            row = i // 3
            col = i % 3

            card = MethodCard(
                method_num=method_data["id"],
                method_name=method_data["name"],
                method_title=method_data.get("description")
                             or method_data["standard"],
                category=method_data.get("category", "Диэлектрики"),
                color=palette[i % len(palette)]
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
        # Разделитель секций
        separator = WidgetFactory.create_divider()
        self.content_layout.addWidget(separator)

        # Create section header with "View all" button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 10, 0, 8)

        recent_label = self.create_section_title("Последние исследования", 20)
        header_layout.addWidget(recent_label)
        header_layout.addStretch()

        all_measures_btn = WidgetFactory.create_button(
            "все исследования >",
            style="link"
        )
        all_measures_btn.clicked.connect(self.show_all_measurements)
        header_layout.addWidget(all_measures_btn)

        self.content_layout.addLayout(header_layout)

        # Create scroll area for recent measurements
        self.recent_scroll = WidgetFactory.create_scroll_area()
        self.recent_widget = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_widget)
        self.recent_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.recent_layout.setSpacing(10)
        self.recent_scroll.setWidget(self.recent_widget)

        self.content_layout.addWidget(self.recent_scroll)

        # Load measurements
        self.load_recent_measurements()

    def setup_recent_reports(self):
        """Setup recent reports section"""
        # Section header with "View all" button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)

        reports_label = self.create_section_title("Последние отчёты", 20)
        header_layout.addWidget(reports_label)
        header_layout.addStretch()

        all_reports_btn = WidgetFactory.create_button(
            "все отчёты >",
            style="link"
        )
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
            ("Отчёт #СВЧФ_1_01122024", "20.11.2025", "СВЧФ", "Исследование СВЧ ферритов"),
            ("Отчёт #СВЧФ_3_01122024", "20.11.2025", "СВЧФ", "Повторные замеры"),
            ("Отчёт #СО_1_01122024", "19.11.2025", "СО", "Стержневые образцы"),
            ("Отчёт #ФРЧ_2_01122024", "18.11.2025", "ФРЧ", "Фиксированная частота")
        ]

        for i, (title, date, method_type, color) in enumerate(reports):
            row = i // 2
            col = i % 2
            report_card = self.create_report_card(title, date, method_type, color)
            grid_layout.addWidget(report_card, row, col)

        self.content_layout.addWidget(grid_widget)

    def open_measurement_page(self, method_id):
        """Open measurement page with selected method"""

        # Получаем главное окно
        main_window = self.parent()
        while main_window and not isinstance(main_window, QMainWindow):
            main_window = main_window.parent()

        if main_window and hasattr(main_window, 'open_new_measurement_page'):
            main_window.open_new_measurement_page(method_id)
        else:
            self.navigate_to_new_measurement(method_id)

    def navigate_to_new_measurement(self, method_id):
        """Alternative navigation to new measurement page"""

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
        # Ищем главное окно
        from PyQt6.QtWidgets import QMainWindow

        widget = self
        main_window = None

        while widget:
            if isinstance(widget, QMainWindow):
                main_window = widget
                break
            widget = widget.parent()

        if main_window and hasattr(main_window, 'page_stack'):
            # Переключаемся на страницу измерений
            main_window.page_stack.setCurrentWidget(main_window.measures_page)

            # Активируем кнопку "Измерения" в сайдбаре (индекс 2)
            if hasattr(main_window, 'sidebar') and hasattr(main_window.sidebar, 'nav_buttons'):
                if len(main_window.sidebar.nav_buttons) >= 3:
                    main_window.sidebar.set_active_button(main_window.sidebar.nav_buttons[2])

    def show_all_reports(self):
        """Navigate to reports page"""
        # Ищем главное окно
        from PyQt6.QtWidgets import QMainWindow

        widget = self
        main_window = None

        while widget:
            if isinstance(widget, QMainWindow):
                main_window = widget
                break
            widget = widget.parent()

        if main_window and hasattr(main_window, 'page_stack'):
            # Переключаемся на страницу отчетов
            main_window.page_stack.setCurrentWidget(main_window.reports_page)

            # Активируем кнопку "Отчёты" в сайдбаре (индекс 3)
            if hasattr(main_window, 'sidebar') and hasattr(main_window.sidebar, 'nav_buttons'):
                if len(main_window.sidebar.nav_buttons) >= 4:
                    main_window.sidebar.set_active_button(main_window.sidebar.nav_buttons[3])

    def load_recent_measurements(self):
        """Load and display recent measurements (2 per row, 4 total)"""
        # Clear existing content
        for i in reversed(range(self.recent_layout.count())):
            item = self.recent_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Get real measurements from backend
        real_measures = self.backend.query("measure_data", 0)

        # Статические данные для 4х карточек
        static_measurements = [
            {
                'id_m': 'demo1',
                'method_id': 1,
                'title': '001',
                'time': '20.11.2024 14:30',
                'y_samples': {
                    '1': {
                        'name': 'Керамика А',
                        'tgo': 1.23e-4,
                        'E': 9.87
                    }
                }
            },
            {
                'id_m': 'demo2',
                'method_id': 2,
                'title': '002',
                'time': '19.11.2024 11:45',
                'y_samples': {
                    '1': {
                        'name': 'Полимер Б',
                        'tgo': 2.34e-4,
                        'E': 3.21
                    }
                }
            },
            {
                'id_m': 'demo3',
                'method_id': 3,
                'title': '003',
                'time': '18.11.2024 16:20',
                'y_samples': {
                    '1': {
                        'name': 'Стекло В',
                        'tgo': 3.45e-4,
                        'E': 4.56
                    }
                }
            },
            {
                'id_m': 'demo4',
                'method_id': 4,
                'title': '004',
                'time': '17.11.2024 09:15',
                'y_samples': {
                    '1': {
                        'name': 'Феррит Г',
                        'tgo': 4.56e-4,
                        'E': 7.89
                    }
                }
            }
        ]

        # Если есть реальные измерения, используем их (максимум 4)
        if real_measures:
            # Берем максимум 4 последних реальных измерений
            recent_real = real_measures[-4:] if len(real_measures) > 4 else real_measures

            # Создаем контейнер для сетки 2x2
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(12)
            grid_layout.setContentsMargins(0, 0, 0, 0)

            # Добавляем реальные измерения
            for i, measure in enumerate(recent_real):
                row = i // 2
                col = i % 2
                measure_card = self.create_measurement_card(measure)
                grid_layout.addWidget(measure_card, row, col)

            # Если реальных измерений меньше 4, дополняем статическими
            if len(recent_real) < 4:
                start_index = len(recent_real)
                for i in range(start_index, 4):
                    row = i // 2
                    col = i % 2
                    static_card = self.create_measurement_card(static_measurements[i])
                    grid_layout.addWidget(static_card, row, col)

            self.recent_layout.addWidget(grid_widget)
        else:
            # Если нет реальных измерений, показываем 4 статические карточки
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(12)
            grid_layout.setContentsMargins(0, 0, 0, 0)

            for i, measure_data in enumerate(static_measurements):
                row = i // 2
                col = i % 2
                measure_card = self.create_measurement_card(measure_data)
                grid_layout.addWidget(measure_card, row, col)

            self.recent_layout.addWidget(grid_widget)

    def create_measurement_card(self, measure):
        """Create a measurement card for the home page with graph preview on left"""
        from widgets import ModernCard
        from PyQt6.QtWidgets import QFrame
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QSize

        card = ModernCard()
        card.setProperty("clickable", True)
        card.setFixedHeight(140)  # Уменьшаем высоту для компактности
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(15)

        # ЛЕВАЯ ЧАСТЬ: Мини-график с изображением
        graph_container = QFrame()
        graph_container.setObjectName("graphPreview")
        graph_container.setFixedSize(160, 100)  # Фиксированный размер для графика

        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)

        if measure.get('x') and measure.get('y_res'):
            # Мини-график АЧХ из данных записи (спарклайн)
            from widgets.sparkline import SparklineWidget
            graph_layout.addWidget(SparklineWidget(
                measure['x'], measure['y_res'], parent=graph_container))
        else:
            # Нет кривой (демо-записи) — статичная картинка/заглушка
            graph_image = QLabel()
            graph_image.setFixedSize(150, 90)
            graph_image.setScaledContents(True)

            try:
                pixmap = QPixmap("img/graf.png")
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(graph_image.size(),
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    graph_image.setPixmap(pixmap)
                else:
                    graph_image.setText("📊")
                    graph_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    graph_image.setProperty("role", "imagePlaceholder")
            except Exception as e:
                print(f"Ошибка загрузки изображения: {e}")
                graph_image.setText("📊")
                graph_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
                graph_image.setProperty("role", "imagePlaceholder")

            graph_layout.addWidget(graph_image)

        card_layout.addWidget(graph_container)

        # ОСТАЛЬНАЯ ЧАСТЬ КОДА (без изменений)
        # ПРАВАЯ ЧАСТЬ: Информация об измерении
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок измерения
        method_names = {
            1: "ФРЧ", 2: "ФРД", 3: "СО", 4: "СВЧФ1", 5: "ЩР", 6: "СВЧФ2"
        }

        method_id = measure.get('method_id', 1)
        method_name = method_names.get(method_id, f"Метод {method_id}")

        title = WidgetFactory.create_label(
            f"{method_name} • #{measure.get('title', 'Unknown')}",
            role="h3"
        )

        # Время измерения
        time_str = measure.get('time', 'Неизвестно')
        time_label = WidgetFactory.create_label(
            f"📅 {time_str}",
            role="caption"
        )

        # Информация об образце
        sample_info = WidgetFactory.create_label("", role="caption")
        if measure.get('y_samples'):
            sample = list(measure['y_samples'].values())[0]
            sample_name = sample.get('name', 'Неизвестно')
            sample_info.setText(f"📋 {sample_name}")

        # Результаты (если есть)
        results_label = WidgetFactory.create_label("", role="accent")
        if measure.get('y_samples'):
            sample = list(measure['y_samples'].values())[0]
            if 'tgo' in sample and 'E' in sample:
                results_label.setText(f"📈 tgδ: {sample['tgo']:.2e} • ε: {sample['E']:.2f}")

        # Добавляем все элементы
        info_layout.addWidget(title)
        info_layout.addWidget(time_label)
        if sample_info.text():
            info_layout.addWidget(sample_info)
        if results_label.text():
            info_layout.addWidget(results_label)

        info_layout.addStretch()

        card_layout.addLayout(info_layout, 1)  # 1 - растягиваем на всю доступную ширину

        # Сделать карточку кликабельной
        card.mousePressEvent = lambda event, mid=measure['id_m']: self.open_measurement(mid, event)

        return card

    def open_measurement(self, measure_id, event):
        """Open measurement details (пропускаем для демо-измерений)"""
        if measure_id.startswith('demo'):
            print(f"Демо-измерение #{measure_id} - переход невозможен")
            return
        self.open_measure_callback(measure_id)

    def create_report_card(self, title, date, method_type, description):
        """Create a report card widget"""
        from widgets import ModernCard

        card = ModernCard()
        card.setProperty("clickable", True)
        card.setFixedHeight(120)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # Report icon - ОДИНАКОВЫЙ для всех отчётов
        icon_widget = WidgetFactory.create_label("📄", role="iconBadge", align="center")
        icon_widget.setFixedSize(50, 50)

        # Report info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Title
        report_title = WidgetFactory.create_label(title, role="h3")

        # Method type (цветной тег)
        method_label = QLabel(f" {method_type} ")
        method_label.setProperty("role", "methodBadge")

        # Description
        desc_label = WidgetFactory.create_label(description, role="small")

        # Date
        date_label = WidgetFactory.create_label(f"📅 {date}", role="small")

        # Верхняя строка: заголовок и тег метода
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        top_row.addWidget(report_title)
        top_row.addWidget(method_label)
        top_row.addStretch()

        info_layout.addLayout(top_row)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(date_label)
        info_layout.addStretch()

        card_layout.addWidget(icon_widget)
        card_layout.addLayout(info_layout, 1)

        # Connect click
        card.mousePressEvent = lambda event, t=title: self.open_report(t, event)

        return card

    def open_report(self, report_title, event):
        """Open report - в реальном приложении здесь будет переход на страницу отчета"""
        print(f"Opening report: {report_title}")
        # Можно добавить навигацию на страницу отчетов с предвыбранным отчетом

    def refresh_page(self):
        """Refresh page content"""
        self.load_recent_measurements()
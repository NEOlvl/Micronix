"""
New measurement page
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QScrollArea, QFormLayout,
                             QLineEdit, QSpinBox, QComboBox, QGroupBox)
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import ModernCard, HeaderWidget
from styles import Styles


class NewMeasurementPage(BasePage):
    """Page for creating new measurements.

    Карточки методов и форма параметров строятся по реестру
    методов backend (ТЗ-9): inputs[] -> поля формы, validate() ->
    проверка перед стартом (ТЗ-7).
    """
    measurement_started = pyqtSignal(dict)
    start_measurement_process = pyqtSignal(dict)

    def __init__(self, backend, parent=None):
        # Сначала устанавливаем атрибуты
        self.backend = backend
        self._method_meta = {m['id']: m
                             for m in backend.list_methods()}
        self.selected_method = next(iter(self._method_meta), None)
        self.selected_variant = None
        self._param_fields = {}

        # Потом вызываем родительский конструктор
        super().__init__("", "", parent)  # Пустые заголовки, т.к. используем кастомный header

        # Удаляем стандартный layout от BasePage
        if self.layout:
            # Очищаем layout, но не удаляем его
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.setup_ui()

    def setup_ui(self):
        """Setup page UI"""
        # Создаем новый главный layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Setup custom header
        self.setup_custom_header(main_layout)

        # Setup content
        self.setup_content(main_layout)

    def setup_custom_header(self, parent_layout):
        """Setup custom header - ПРАВИЛЬНОЕ ПРОДОЛЖЕНИЕ САЙДБАРА"""
        self.header = QWidget()
        self.header.setFixedHeight(100)
        self.header.setContentsMargins(0, 0, 0, 0)
        self.header.setStyleSheet(f"""
            QWidget {{
                background: #7879F1;
                border: none;
                margin: 0;
                padding: 0;
            }}
        """)

        parent_layout.addWidget(self.header)
        parent_layout.setContentsMargins(0, 0, 0, 0)

    def setup_content(self, parent_layout):
        """Setup page content"""
        # Create main content widget with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
                margin: 0;
                padding: 0;
            }
        """)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(30, 20, 30, 20)  # Восстанавливаем отступы только для контента
        self.content_layout.setSpacing(25)

        # Method selection
        self.setup_method_selection(self.content_layout)

        # Method parameters
        self.setup_method_parameters(self.content_layout)

        # Action buttons
        self.setup_action_buttons(self.content_layout)

        self.content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        parent_layout.addWidget(scroll_area, 1)

    def setup_method_selection(self, parent_layout):
        """Setup method selection section - БЕЗ ЗАГОЛОВКОВ"""

        # Method cards grid - теперь 3 карточки в 2 ряда = 6 карточки
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Карточки методов — из реестра backend (ТЗ-9)
        for i, meta in enumerate(self._method_meta.values()):
            row = i // 3
            col = i % 3
            card = self.create_method_card(
                meta['id'], meta['name'],
                meta.get('description') or meta['standard'], "#7879F1")
            card.method_id = meta['id']
            grid_layout.addWidget(card, row, col)

        parent_layout.addWidget(grid_widget)

    def create_method_card(self, method_id, name, description, color="#7879F1"):
        """Create a method selection card"""
        card = ModernCard()
        card.setMinimumHeight(140)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        # Сохраняем ID метода в объекте карточки
        card.method_id = method_id

        # ВСЕГДА используем один цвет для обводки и текста - фиолетовый как у первого метода
        primary_color = "#7879F1"  # Фиксированный цвет для всего

        # Highlight if selected
        if method_id == self.selected_method:
            card.setStyleSheet(f"""
                ModernCard {{
                    background: rgba(40, 41, 44, 0.9);
                    border: 2px solid {primary_color};
                    border-radius: 12px;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                ModernCard {{
                    background: rgba(30, 31, 34, 0.8);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                }}
            """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        # Method header - БЕЗ бейджа в правом углу
        header_layout = QHBoxLayout()

        # Все названия методов одним цветом - фиолетовым
        method_name = QLabel(name)
        method_name.setStyleSheet(f"""
            QLabel {{
                color: {primary_color};
                font-size: 18px;
                font-weight: 600;
            }}
        """)

        header_layout.addWidget(method_name)
        header_layout.addStretch()  # Добавляем растяжку чтобы название было слева

        # Description
        method_desc = QLabel(description)
        method_desc.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                line-height: 1.4;
            }}
        """)
        method_desc.setWordWrap(True)

        card_layout.addLayout(header_layout)
        card_layout.addWidget(method_desc)
        card_layout.addStretch()

        # Connect click
        card.mousePressEvent = lambda e, mid=method_id: self.select_method(mid)

        return card

    def setup_method_parameters(self, parent_layout):
        """Форма параметров — генерируется по inputs[] метода (ТЗ-9)."""
        meta = self._method_meta.get(self.selected_method)
        title = WidgetFactory.create_label(
            f"Параметры исследования: "
            f"{meta['name'] if meta else self.selected_method}",
            font_size=18,
            bold=True
        )
        parent_layout.addWidget(title)

        # Parameters container
        params_container = QWidget()
        params_layout = QVBoxLayout(params_container)
        params_layout.setSpacing(20)

        params_layout.addWidget(self.create_resonator_settings_group())
        params_layout.addWidget(self._make_error_label())

        parent_layout.addWidget(params_container)

    def _make_error_label(self):
        """Метка ошибок валидации параметров."""
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        self.error_label.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                font-size: 13px;
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 6px;
                padding: 10px;
            }
        """)
        return self.error_label

    def create_resonator_settings_group(self):
        """Группа параметров: inputs[] метода + общие поля среды."""
        group = QGroupBox("Предварительная настройка перед началом измерения")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 12px;
                background: rgba(40, 41, 44, 0.6);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
            }}
        """)

        layout = QFormLayout(group)
        layout.setVerticalSpacing(12)
        layout.setHorizontalSpacing(20)

        meta = self._method_meta.get(self.selected_method)
        self._param_fields = {}

        # Вариант расчёта, если метод их имеет (СВЧФ)
        variants = (meta or {}).get('variants')
        if variants:
            if self.selected_variant not in variants:
                self.selected_variant = next(iter(variants))
            self.variant_combo = QComboBox()
            for vid, vname in variants.items():
                self.variant_combo.addItem(vname, vid)
            self.variant_combo.setCurrentIndex(
                list(variants).index(self.selected_variant))
            self.variant_combo.setStyleSheet(Styles.INPUT_FIELD)
            self.variant_combo.currentIndexChanged.connect(
                lambda _: self.select_variant(
                    self.variant_combo.currentData()))
            layout.addRow("Вариант расчёта:", self.variant_combo)
        else:
            self.selected_variant = None

        # Поля по описанию inputs[] метода (ТЗ-9)
        if meta:
            form = self.backend.method_form(
                self.selected_method, self.selected_variant)
            for spec in form['inputs']:
                default = spec.get('default')
                edit = WidgetFactory.create_input(
                    '' if default is None else str(default))
                label = spec['label']
                if spec.get('unit'):
                    label += f", {spec['unit']}"
                if spec.get('bounds'):
                    lo, hi = spec['bounds']
                    label += f" [{lo:g}–{hi:g}]"
                    edit.setToolTip(
                        f"Допустимый диапазон: {lo:g}…{hi:g} "
                        f"{spec.get('unit') or ''}")
                layout.addRow(label + ':', edit)
                self._param_fields[spec['name']] = edit

        # Параметры окружающей среды (общие, ТЗ-7 — данные датчиков)
        self.temp_input = WidgetFactory.create_input("25.0")
        self.humidity_input = WidgetFactory.create_input("50.0")

        layout.addRow("Температура (°C):", self.temp_input)
        layout.addRow("Влажность (%):", self.humidity_input)

        return group

    def setup_action_buttons(self, parent_layout):
        """Setup action buttons section"""
        # Container for buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 20, 0, 0)

        buttons_layout.addStretch()

        # Clear button
        clear_btn = WidgetFactory.create_button("Очистить форму", style="secondary")
        clear_btn.setFixedWidth(150)
        clear_btn.clicked.connect(self.clear_form)

        # Start measurement button
        start_btn = WidgetFactory.create_button("Начать исследование", style="primary")
        start_btn.setFixedWidth(200)
        start_btn.clicked.connect(self.start_measurement)

        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(start_btn)

        parent_layout.addWidget(buttons_container)

    def select_method(self, method_id):
        """Select a different method"""
        self.selected_method = method_id
        self.selected_variant = None

        # Обновляем выделение карточек
        self.update_method_cards_selection()

        # Clear and rebuild parameters section
        self.refresh_parameters()

    def select_variant(self, variant_id):
        """Выбор варианта расчёта (СВЧФ) — пересобирает поля."""
        self.selected_variant = variant_id
        self.refresh_parameters()

    def update_method_cards_selection(self):
        """Update visual selection of method cards"""
        # Находим все карточки методов
        grid_widget = self.findChild(QWidget)  # Ищем grid widget
        if grid_widget:
            for child in grid_widget.findChildren(QWidget):
                if child.__class__.__name__ == "ModernCard" and hasattr(child, 'method_id'):
                    # Всегда используем один цвет для выделения
                    border_color = "#7879F1"

                    # Проверяем, это ли метод выбран
                    if child.method_id == self.selected_method:
                        # Выделяем выбранную карточку фиолетовым
                        child.setStyleSheet(f"""
                            ModernCard {{
                                background: rgba(40, 41, 44, 0.9);
                                border: 2px solid {border_color};
                                border-radius: 12px;
                            }}
                        """)
                    else:
                        # Сбрасываем стиль для остальных
                        child.setStyleSheet(f"""
                            ModernCard {{
                                background: rgba(30, 31, 34, 0.8);
                                border: 1px solid rgba(255, 255, 255, 0.1);
                                border-radius: 12px;
                            }}
                        """)

    def refresh_parameters(self):
        """Refresh parameters section when method changes"""
        # Находим родительский scroll area
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            # Создаем новый контент
            content_widget = QWidget()
            self.content_layout = QVBoxLayout(content_widget)
            self.content_layout.setContentsMargins(30, 20, 30, 20)
            self.content_layout.setSpacing(25)

            # Method selection
            self.setup_method_selection(self.content_layout)

            # Method parameters (обновляем)
            self.setup_method_parameters(self.content_layout)

            # Action buttons
            self.setup_action_buttons(self.content_layout)

            self.content_layout.addStretch()

            # Устанавливаем новый виджет
            scroll_area.setWidget(content_widget)

    def clear_form(self):
        """Clear all form fields"""
        for edit in self._param_fields.values():
            edit.clear()
        self.temp_input.clear()
        self.humidity_input.clear()
        if hasattr(self, 'error_label'):
            self.error_label.setVisible(False)

    def start_measurement(self):
        """Валидация по inputs[] (ТЗ-7) и старт сессии измерения."""
        if getattr(self, '_measurement_in_progress', False):
            print("Measurement already in progress")
            return

        params = {name: edit.text() for name, edit
                  in self._param_fields.items()}
        params['temperature'] = self.temp_input.text() or '25.0'
        params['humidity'] = self.humidity_input.text() or '50.0'

        errors = self.backend.validate_params(
            self.selected_method, params, self.selected_variant)
        if errors:
            self._show_param_errors(errors)
            return
        self.error_label.setVisible(False)

        self._measurement_in_progress = True
        try:
            meta = self._method_meta.get(self.selected_method, {})
            title = (meta.get('name') or self.selected_method)
            session = self.backend.start_measurement(
                self.selected_method, params,
                title=title, variant=self.selected_variant)
        except Exception as exc:
            self._measurement_in_progress = False
            self._show_param_errors(
                getattr(exc, 'errors', [str(exc)]))
            return

        self.measurement_started.emit({
            'session_id': session.id,
            'measurement_id': session.id,
            'method': self.selected_method,
            'method_name': title,
        })

    def _show_param_errors(self, errors):
        self.error_label.setText('\n'.join(f'• {e}' for e in errors))
        self.error_label.setVisible(True)

    def show_selected_method_notification(self, method_id):
        """Show notification about selected method"""
        meta = self._method_meta.get(method_id, {})
        method_name = meta.get('name', f'Метод {method_id}')

        # Можно добавить временное уведомление в интерфейсе
        notification = QLabel(f"Выбран метод: {method_name}")
        notification.setStyleSheet(f"""
            QLabel {{
                color: #7879F1;
                font-size: 14px;
                font-weight: 600;
                background: rgba(120, 121, 241, 0.1);
                border: 1px solid #7879F1;
                border-radius: 6px;
                padding: 8px 16px;
                margin: 10px 0;
            }}
        """)
        notification.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Добавляем уведомление в начало контента
        self.content_layout.insertWidget(0, notification)

        # Убираем уведомление через 3 секунды
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: notification.deleteLater())
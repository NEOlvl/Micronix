"""
Measurement process widget (embedded version) with JSON support
"""

import random
import json
import os
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFrame,
    QScrollArea, QFileDialog
)
import numpy as np
import pyqtgraph as pg

from widgets import ModernCard, LoadingSpinner
from widgets.measurement_graph import MeasurementGraphWidget
from styles import repolish


class MeasurementProcessWidget(QWidget):
    """Widget showing measurement progress (embedded version) with JSON support"""

    # Сигналы - объявляем на уровне класса
    measurement_finished = pyqtSignal()
    measurement_stopped = pyqtSignal()
    method_selection_requested = pyqtSignal(int)

    # Этапы измерения
    STAGES = [
        "Подготовка оборудования",
        "Калибровка резонатора",
        "Измерение без образца",
        "Ожидание образца",
        "Сбор данных образца",
        "Обработка данных",
        "Сохранение результатов"
    ]

    def __init__(self, backend, measurement_data, parent=None):
        """Constructor with measurement_data dict"""
        super().__init__(parent)
        self.backend = backend
        self.measurement_data = measurement_data
        self.measure_id = measurement_data.get('measurement_id', 'unknown')
        self.method_id = measurement_data.get('method', 1)
        # Сессия измерения backend (ТЗ-7): sweep -> резонанс -> расчёт
        self.session = None
        sessions = getattr(backend, 'sessions', None)
        if sessions is not None:
            self.session = sessions.get(
                measurement_data.get('session_id'))
        self.current_stage = 0
        self.samples_added = []
        self.is_active = True
        self.waiting_for_sample = False
        self._base_done = False

        # Для работы с файлами данных
        self.data_files = []
        self.current_file_index = 0
        self.current_data_file = None

        # Инициализация всех атрибутов
        self.file_panel = None
        self.select_file_btn = None
        self.file_info_label = None
        self.info_layout = None
        self.info_content = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        self.setMinimumSize(1200, 800)

        # Главный layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.setup_header(main_layout)

        # Progress info
        self.setup_progress_info(main_layout)

        # Main content area
        self.setup_content_area(main_layout)

    def setup_header(self, parent_layout):
        """Setup header with title and buttons"""
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setFixedHeight(70)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 0, 25, 0)
        header_layout.setSpacing(15)

        # Title
        self.title_label = QLabel("Исследование #...")
        self.title_label.setProperty("role", "h2")

        # Progress percentage
        self.progress_percent = QLabel("0%")
        self.progress_percent.setProperty("role", "percent")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_percent)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Back button
        back_btn = QPushButton("Назад")
        back_btn.setProperty("btnStyle", "secondary")
        back_btn.setMinimumWidth(100)
        back_btn.clicked.connect(self.return_to_creation)

        # Stop button
        stop_btn = QPushButton("Остановить")
        stop_btn.setProperty("btnStyle", "danger")
        stop_btn.setMinimumWidth(120)
        stop_btn.clicked.connect(self.stop_measurement)

        buttons_layout.addWidget(back_btn)
        buttons_layout.addWidget(stop_btn)

        header_layout.addLayout(buttons_layout)
        parent_layout.addWidget(header)

    def setup_progress_info(self, parent_layout):
        """Setup progress information section"""
        progress_widget = QWidget()
        progress_widget.setObjectName("progressPanel")
        progress_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        progress_widget.setFixedHeight(140)

        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(30, 20, 30, 20)
        progress_layout.setSpacing(15)

        # Stage info
        stage_layout = QHBoxLayout()

        self.stage_label = QLabel(f"Этап 1: {self.STAGES[0]}")
        self.stage_label.setProperty("role", "h3")

        self.stage_desc = QLabel("Начало процесса измерения...")
        self.stage_desc.setProperty("role", "subtitle")

        stage_layout.addWidget(self.stage_label)
        stage_layout.addWidget(self.stage_desc)
        stage_layout.addStretch()

        progress_layout.addLayout(stage_layout)

        # Progress bars
        bars_layout = QHBoxLayout()
        bars_layout.setSpacing(10)

        self.bars = []
        for i in range(len(self.STAGES)):
            bar_container = self.create_progress_bar(i == 0)
            bars_layout.addWidget(bar_container)
            self.bars.append(bar_container.findChild(QWidget))

        progress_layout.addLayout(bars_layout)
        parent_layout.addWidget(progress_widget)

    def create_progress_bar(self, is_active=False):
        """Create a progress bar segment"""
        container = QWidget()
        container.setFixedHeight(8)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        bar = QWidget()
        bar.setObjectName("progressSeg")
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        if is_active:
            bar.setProperty("state", "active")
            bar.setFixedWidth(0)
        else:
            # Неактивный сегмент — видимый трек на всю ширину
            # контейнера (фиксировать ширину нельзя: до показа
            # она равна 0 и сегмент был бы невидим).
            bar.setProperty("state", "todo")

        layout.addWidget(bar)
        return container

    def setup_content_area(self, parent_layout):
        """Setup main content area with graph and controls"""
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Graph area (70% ширины)
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(10)

        # Graph title
        graph_title = QLabel("График измерения")
        graph_title.setProperty("role", "h3")
        graph_title.setContentsMargins(0, 5, 0, 5)
        graph_layout.addWidget(graph_title)

        # Main graph widget
        self.graph = MeasurementGraphWidget()
        self.graph.setMinimumHeight(500)
        graph_layout.addWidget(self.graph, 1)

        content_layout.addWidget(graph_container, 7)

        # Side panel (30% ширины)
        side_panel = self.create_side_panel()
        content_layout.addWidget(side_panel, 3)

        parent_layout.addWidget(content_widget, 1)

        # Добавляем панель для работы с файлами
        self.setup_file_panel(parent_layout)

        # Скрываем панель по умолчанию
        if self.file_panel:
            self.file_panel.hide()

    def setup_file_panel(self, parent_layout):
        """Панель для выбора файлов данных"""
        self.file_panel = ModernCard()
        self.file_panel.setFixedHeight(120)

        file_layout = QVBoxLayout(self.file_panel)
        file_layout.setContentsMargins(20, 15, 20, 15)
        file_layout.setSpacing(10)

        # Верхняя строка: заголовок и кнопка
        top_row = QHBoxLayout()

        # Заголовок
        file_title = QLabel("Работа с данными измерений")
        file_title.setProperty("role", "h3")

        # Кнопка выбора файла
        self.select_file_btn = QPushButton("Выбрать файл данных")
        self.select_file_btn.setProperty("btnStyle", "secondary")
        self.select_file_btn.clicked.connect(self.select_data_file)

        top_row.addWidget(file_title)
        top_row.addStretch()
        top_row.addWidget(self.select_file_btn)

        # Информация о выбранном файле
        self.file_info_label = QLabel("Файл не выбран")
        self.file_info_label.setProperty("role", "caption")
        self.file_info_label.setWordWrap(True)

        file_layout.addLayout(top_row)
        file_layout.addWidget(self.file_info_label)

        parent_layout.addWidget(self.file_panel)

    def create_side_panel(self):
        """Create the side panel with controls and info"""
        panel = ModernCard()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(20)

        # Status section
        status_widget = self.create_status_section()
        panel_layout.addWidget(status_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("divider")
        separator.setFixedHeight(1)
        panel_layout.addWidget(separator)

        # Sample input section
        sample_widget = self.create_sample_input_section()
        panel_layout.addWidget(sample_widget)

        # Action buttons
        buttons_widget = self.create_action_buttons()
        panel_layout.addWidget(buttons_widget)

        panel_layout.addStretch()

        return panel

    def create_status_section(self):
        """Create status section with spinner and messages"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Loading spinner
        self.loading_spinner = LoadingSpinner()
        layout.addWidget(self.loading_spinner, 0, Qt.AlignmentFlag.AlignHCenter)

        # Status title
        self.status_title = QLabel("Исследование в процессе")
        self.status_title.setProperty("role", "h3")
        self.status_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status description
        self.status_desc = QLabel("Пожалуйста, ожидайте завершения процесса.")
        self.status_desc.setProperty("role", "subtitle")
        self.status_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_desc.setWordWrap(True)

        layout.addWidget(self.status_title)
        layout.addWidget(self.status_desc)

        return widget

    def create_sample_input_section(self):
        """Create sample input section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Title
        sample_title = QLabel("Добавление образца")
        sample_title.setProperty("role", "h3")
        sample_title.setContentsMargins(0, 0, 0, 5)

        # Input field
        self.sample_name_input = QLineEdit()
        self.sample_name_input.setPlaceholderText("Введите имя образца")
        self.sample_name_input.setEnabled(False)

        layout.addWidget(sample_title)
        layout.addWidget(self.sample_name_input)

        return widget

    def create_action_buttons(self):
        """Create action buttons section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Continue button
        self.continue_btn = QPushButton("Добавить образец")
        self.continue_btn.setProperty("btnStyle", "primary")
        self.continue_btn.clicked.connect(self.add_sample)
        self.continue_btn.setEnabled(False)
        self.continue_btn.setFixedHeight(50)

        # Finish button
        self.finish_btn = QPushButton("Завершить исследование")
        self.finish_btn.setProperty("btnStyle", "secondary")
        self.finish_btn.clicked.connect(self.finish_measurement)
        self.finish_btn.setEnabled(False)
        self.finish_btn.setFixedHeight(50)

        layout.addWidget(self.continue_btn)
        layout.addWidget(self.finish_btn)

        return widget

    def create_info_panel(self):
        """Create side info panel"""
        panel = ModernCard()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)

        # Title
        info_title = QLabel("Информация об измерении")
        info_title.setProperty("role", "h3")
        panel_layout.addWidget(info_title)

        # Scrollable info content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.info_content = QWidget()
        self.info_layout = QVBoxLayout(self.info_content)
        self.info_layout.setSpacing(15)
        self.info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.info_content)
        panel_layout.addWidget(scroll_area, 1)

        return panel

    def load_initial_graph(self):
        """Загрузка начального пустого графика"""
        try:
            if hasattr(self, 'graph') and self.graph:
                self.graph.plot_widget.clear()

                # Добавляем подпись
                text = pg.TextItem("Ожидание данных...", color='#7879F1', fill='#1a1b1e80')
                text.setPos(10.0, -15)
                self.graph.plot_widget.addItem(text)

                print("Initial graph loaded")

        except Exception as e:
            print(f"Error loading initial graph: {e}")

    def start_measurement_process(self):
        """Start the measurement process"""
        method_name = (self.measurement_data.get('method_name')
                       or (self.session.method.name if self.session
                           else str(self.method_id)))
        if hasattr(self, 'title_label'):
            self.title_label.setText(f"Исследование: {method_name}")

        # Загружаем начальный график
        self.load_initial_graph()

        # Запускаем прогресс
        self.start_progress_animation()

    def start_progress_animation(self):
        """Start the progress bar animation"""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(500)  # 500ms = 0.5 секунды

    def update_progress(self):
        """Update progress bars and stages"""
        if not self.is_active:
            return

        # Если ждём образец - не продвигаем автоматически
        if self.waiting_for_sample:
            return

        # Увеличиваем прогресс текущего этапа
        if self.current_stage < len(self.bars):
            current_bar = self.bars[self.current_stage]
            if current_bar:
                current_width = current_bar.width()
                parent_width = current_bar.parent().width()

                if current_width < parent_width * 0.95:
                    increment = parent_width * 0.002  # 0.2% за шаг
                    new_width = min(current_width + increment, parent_width * 0.95)
                    current_bar.setFixedWidth(int(new_width))

                    # Обновляем процент
                    total_progress = sum(bar.width() for bar in self.bars if bar)
                    total_width = sum(bar.parent().width() for bar in self.bars)
                    percent = int((total_progress / total_width) * 100)

                    if hasattr(self, 'progress_percent'):
                        self.progress_percent.setText(f"{percent}%")

                else:
                    # Завершаем текущий сегмент и переходим дальше
                    current_bar.setFixedWidth(parent_width)
                    current_bar.setProperty("state", "done")
                    repolish(current_bar)
                    self.current_stage += 1

                    if self.current_stage < len(self.STAGES):
                        next_bar = self.bars[self.current_stage]
                        if next_bar:
                            next_bar.setProperty("state", "active")
                            repolish(next_bar)
                            next_bar.setFixedWidth(0)
                        # Активируем следующий этап
                        self.update_stage_info()

                        if self.current_stage == 2:
                            # Реальный съём АЧХ без образца (ТЗ-9)
                            self._measure_base()
                        elif self.current_stage == 3:  # "Ожидание образца"
                            self.wait_for_sample()
                        elif self.current_stage >= 4:
                            # Сбор данных образцов — ждём действий
                            # оператора (ещё образец / завершить)
                            self.progress_timer.stop()
                            if hasattr(self, 'finish_btn'):
                                self.finish_btn.setEnabled(
                                    bool(self.samples_added))
                    else:
                        # Все этапы завершены
                        self.complete_measurement()

        # Периодически обновляем график
        if random.random() < 0.05:
            self.update_live_graph()

    def update_stage_info(self):
        """Update stage information display"""
        if self.current_stage < len(self.STAGES):
            stage_text = f"Этап {self.current_stage + 1}: {self.STAGES[self.current_stage]}"

            if hasattr(self, 'stage_label'):
                self.stage_label.setText(stage_text)

            # Обновляем описание этапа
            descriptions = [
                "Инициализация оборудования и проверка соединений...",
                "Выполняется калибровка резонатора...",
                "Измерение пустого резонатора...",
                "Ожидание добавления образца...",
                "Обработка результатов измерений...",
                "Сохранение данных в базу..."
            ]

            if self.current_stage < len(descriptions):
                desc_text = descriptions[self.current_stage]
                if hasattr(self, 'stage_desc'):
                    self.stage_desc.setText(desc_text)

    def wait_for_sample(self):
        """Ожидание установки образца"""
        self.waiting_for_sample = True

        # Останавливаем автоматический прогресс
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

        # Обновляем статус
        if hasattr(self, 'status_title'):
            self.status_title.setText("Ожидание образца")

        if hasattr(self, 'status_desc'):
            self.status_desc.setText("Вставьте образец в установку, затем нажмите 'Продолжить'")

        # Активируем кнопку Продолжить
        if hasattr(self, 'continue_btn'):
            self.continue_btn.setText("Продолжить (образец установлен)")
            self.continue_btn.setEnabled(True)

            # Отключаем старые соединения
            try:
                self.continue_btn.clicked.disconnect()
            except:
                pass

            self.continue_btn.clicked.connect(self.sample_installed)

        # Показываем панель файлов
        if self.file_panel:
            self.file_panel.show()

        # Показываем инструкцию
        self.show_sample_instruction()

    def show_sample_instruction(self):
        """Показ инструкции по установке образца"""
        # Создаём info_layout если ещё не создан
        if not hasattr(self, 'info_layout') or self.info_layout is None:
            # Создаём временный контейнер
            temp_widget = QWidget()
            self.info_layout = QVBoxLayout(temp_widget)
            self.info_layout.setSpacing(15)

        # Очищаем панель информации
        for i in reversed(range(self.info_layout.count())):
            item = self.info_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Добавляем инструкцию
        instruction = QLabel("""
        Инструкция:
        1. Убедитесь, что установка включена
        2. Вставьте образец в резонатор
        3. Закрепите образец согласно методике
        4. Убедитесь в отсутствии зазоров
        5. Нажмите 'Продолжить'
        """)
        instruction.setProperty("role", "infoBox")
        instruction.setWordWrap(True)

        self.info_layout.addWidget(instruction)

    def _measure_base(self):
        """Реальный съём АЧХ пустого резонатора через сессию (ТЗ-9)."""
        if self.session is None:
            return
        try:
            res = self.session.measure_base()
            sweep = self.session.base['sweep']
            x_ghz = [f / 1e9 for f in sweep['frequencies']]
            self.graph.plot_widget.clear()
            self.graph.plot_widget.plot(
                x_ghz, sweep['amplitudes'],
                pen=pg.mkPen(color='#7879F1', width=2),
                name='Без образца')
            self._base_done = True
            self.status_title.setText("АЧХ без образца снята")
            self.status_desc.setText(
                f"Резонанс {res['f0'] / 1e9:.4f} ГГц, "
                f"Q = {res['Q']:.0f}, глубина {res['depth_db']:.1f} дБ")
        except Exception as exc:
            self._fail_stage(f"Ошибка съёма АЧХ: {exc}")

    def _measure_sample(self, name: str):
        """Съём АЧХ с образцом + расчёт метода (ТЗ-9)."""
        if self.session is None:
            return
        try:
            smp = self.session.measure_sample(name)
            sweep = self.session.base['sweep']
            x_ghz = [f / 1e9 for f in sweep['frequencies']]
            self.graph.plot_widget.plot(
                x_ghz, smp.sweep_y,
                pen=pg.mkPen(color='#FF8E53', width=2), name=smp.name)

            v = smp.result.values
            e = v.get('E')
            tgo = v.get('tgo')
            lines = []
            if e is not None:
                lines.append(f"E = {e:.4g}")
            if tgo is not None:
                lines.append(f"tg\u03b4 = {tgo:.4g}")
            for err in smp.result.errors:
                lines.append(f"⚠ {err}")
            for w in smp.result.warnings:
                lines.append(f"⚠ {w}")
            self.status_title.setText(
                f"{smp.name}: измерено" if smp.result.ok
                else f"{smp.name}: результат вне диапазонов")
            self.status_desc.setText('; '.join(lines) or smp.name)
            self.samples_added.append({
                'name': smp.name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'E': e, 'tgo': tgo,
            })
        except Exception as exc:
            self._fail_stage(f"Ошибка измерения образца: {exc}")

    def _fail_stage(self, message: str):
        """Контролируемая остановка этапа с диагностикой."""
        self.is_active = False
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        if hasattr(self, 'status_title'):
            self.status_title.setText("Ошибка измерения")
        if hasattr(self, 'status_desc'):
            self.status_desc.setText(message)

    def sample_installed(self):
        """Образец установлен — реальный съём и расчёт (ТЗ-9)."""
        self.waiting_for_sample = False

        # Скрываем инструкцию если есть info_layout
        if hasattr(self, 'info_layout') and self.info_layout:
            for i in reversed(range(self.info_layout.count())):
                item = self.info_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()

        if hasattr(self, 'status_title'):
            self.status_title.setText("Измерение образца...")

        # Реальный съём АЧХ с образцом и расчёт метода
        name = (self.sample_name_input.text().strip()
                if hasattr(self, 'sample_name_input') else '')
        self._measure_sample(name)

        if not self.is_active:
            return

        # Этап "Сбор данных образца" — заполнен
        self.current_stage = 4
        self.update_stage_info()

        # Активируем поле ввода имени образца
        if hasattr(self, 'sample_name_input'):
            self.sample_name_input.setEnabled(True)
            self.sample_name_input.clear()
            self.sample_name_input.setPlaceholderText(
                "Имя следующего образца")

        # Кнопка "ещё один образец" — возвращает в ожидание установки
        if hasattr(self, 'continue_btn'):
            self.continue_btn.setText("Добавить ещё образец")
            try:
                self.continue_btn.clicked.disconnect()
            except Exception:
                pass
            self.continue_btn.clicked.connect(self.wait_for_sample)
            self.continue_btn.setEnabled(True)

        # Завершение доступно после хотя бы одного образца (ТЗ-7)
        if hasattr(self, 'finish_btn'):
            self.finish_btn.setEnabled(bool(self.samples_added))

    def select_data_file(self):
        """Выбор файла с данными измерений"""
        # Ищем файлы в папке measurement_data
        data_dir = "measurement_data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл данных",
            data_dir,
            "JSON files (*.json);;Text files (*.txt);;All files (*.*)"
        )

        if file_path:
            self.load_data_from_file(file_path)

    def load_data_from_file(self, file_path):
        """Загрузка данных из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Обновляем информацию о файле
            filename = os.path.basename(file_path)

            if hasattr(self, 'file_info_label'):
                self.file_info_label.setText(f"Выбран файл: {filename}")

            # Загружаем данные в график
            if hasattr(self, 'graph') and self.graph.load_data_from_json(data):
                # Автоматически заполняем имя образца из файла
                if hasattr(self, 'sample_name_input'):
                    if 'sample_name' in data:
                        self.sample_name_input.setText(data['sample_name'])
                    elif 'title' in data:
                        self.sample_name_input.setText(data['title'])

                # Сохраняем ссылку на файл
                self.current_data_file = file_path

                return True

        except Exception as e:
            print(f"Error loading file: {e}")
            if hasattr(self, 'file_info_label'):
                self.file_info_label.setText(f"Ошибка загрузки файла: {str(e)}")

        return False

    def add_sample(self):
        """Добавление образца с сохранением данных"""
        sample_name = ""

        if hasattr(self, 'sample_name_input'):
            sample_name = self.sample_name_input.text().strip()

        if not sample_name:
            sample_num = len(self.samples_added) + 1
            sample_name = f"Образец {sample_num}"

        # Сохраняем данные образца
        sample_data = {
            'name': sample_name,
            'method': self.method_id,
            'resonator_params': self.measurement_data.get('resonator_params', {}),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Если есть выбранный файл - добавляем путь
        if self.current_data_file:
            sample_data['data_file'] = self.current_data_file

        # Добавляем в список
        self.samples_added.append(sample_data)

        print(f"Образец добавлен: {sample_name}")
        print(f"Всего образцов: {len(self.samples_added)}")

        # Очищаем форму для следующего образца
        self.reset_for_next_sample()

        # Обновляем информацию о добавленных образцах
        self.update_sample_progress()

    def reset_for_next_sample(self):
        """Сброс формы для следующего образца"""
        # Очищаем поле имени
        if hasattr(self, 'sample_name_input'):
            self.sample_name_input.clear()
            self.sample_name_input.setPlaceholderText("Введите имя следующего образца")

        # Сбрасываем выбранный файл
        if hasattr(self, 'file_info_label'):
            self.file_info_label.setText("Файл не выбран")

        self.current_data_file = None

        # Сбрасываем график к базовому состоянию
        self.load_initial_graph()

        # Обновляем статус
        if hasattr(self, 'status_title'):
            self.status_title.setText("Готов к следующему образцу")

        if hasattr(self, 'status_desc'):
            self.status_desc.setText(f"Можете добавить следующий образец.")

    def update_sample_progress(self):
        """Обновление информации о добавленных образцах"""
        # Просто выводим в консоль
        print("Добавленные образцы:")
        for i, sample in enumerate(self.samples_added, 1):
            print(f"  {i}. {sample['name']} - {sample['timestamp']}")

    def update_live_graph(self):
        """Update graph with simulated live data"""
        # Заглушка - в реальном приложении здесь будет обновление данных с оборудования
        pass

    def complete_measurement(self):
        """Complete the measurement process"""
        self.is_active = False

        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

        if hasattr(self, 'status_title'):
            self.status_title.setText("Исследование завершено")

        if hasattr(self, 'status_desc'):
            self.status_desc.setText("Все этапы измерения успешно выполнены.")

        if hasattr(self, 'finish_btn'):
            self.finish_btn.setEnabled(True)

        if hasattr(self, 'continue_btn'):
            self.continue_btn.setEnabled(False)

        if hasattr(self, 'sample_name_input'):
            self.sample_name_input.setEnabled(False)

    def finish_measurement(self):
        """Сохранить сессию в БД и сформировать PDF-протокол (ТЗ-8)."""
        try:
            self.current_stage = 5
            self.update_stage_info()

            if self.session is not None:
                measure_id = self.session.finish()
                try:
                    pdf_path = self.backend.generate_report(measure_id)
                    report_info = f"Протокол: {pdf_path}"
                except Exception as exc:
                    report_info = f"PDF не создан: {exc}"
            else:
                measure_id = self.measure_id
                report_info = ""

            self.current_stage = 6
            self.update_stage_info()
            for bar in self.bars:
                parent = bar.parent()
                if parent:
                    bar.setFixedWidth(parent.width())
                bar.setProperty("state", "done")
                repolish(bar)
            self.progress_percent.setText("100%")

            if hasattr(self, 'status_title'):
                self.status_title.setText("Результаты сохранены")
            if hasattr(self, 'status_desc'):
                self.status_desc.setText(
                    f"Измерение #{measure_id} сохранено в базе. "
                    f"{report_info}".strip())

            if hasattr(self, 'continue_btn'):
                self.continue_btn.setEnabled(False)
            if hasattr(self, 'finish_btn'):
                self.finish_btn.setEnabled(False)

            self.measurement_finished.emit()

        except Exception as e:
            self._fail_stage(f"Ошибка при завершении измерения: {e}")

    def stop_measurement(self):
        """Stop the measurement process"""
        self.is_active = False

        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

        if hasattr(self, 'status_title'):
            self.status_title.setText("Исследование остановлено")

        if hasattr(self, 'status_desc'):
            self.status_desc.setText("Процесс измерения был прерван пользователем.")

        # Отключаем кнопки
        if hasattr(self, 'continue_btn'):
            self.continue_btn.setEnabled(False)

        if hasattr(self, 'finish_btn'):
            self.finish_btn.setEnabled(False)

        if hasattr(self, 'sample_name_input'):
            self.sample_name_input.setEnabled(False)

        # Эмитируем сигнал остановки
        self.measurement_stopped.emit()

    def return_to_creation(self):
        """Return to measurement creation page"""
        self.stop_measurement()
        self.measurement_finished.emit()

    def closeEvent(self, event):
        """Handle close event"""
        self.stop_measurement()
        super().closeEvent(event)
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
from styles import Styles


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
        self.current_stage = 0
        self.samples_added = []
        self.is_active = True
        self.waiting_for_sample = False

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
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            QWidget {{
                background: {Styles.BACKGROUND_MEDIUM};
                border-bottom: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 0, 25, 0)
        header_layout.setSpacing(15)

        # Title
        self.title_label = QLabel("Исследование #...")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
            }
        """)

        # Progress percentage
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet(f"""
            QLabel {{
                color: {Styles.PRIMARY};
                font-size: 20px;
                font-weight: 700;
                background: transparent;
            }}
        """)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_percent)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Back button
        back_btn = QPushButton("Назад")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid {Styles.BORDER_MEDIUM};
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        back_btn.clicked.connect(self.return_to_creation)

        # Stop button
        stop_btn = QPushButton("Остановить")
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.4);
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.3);
            }}
        """)
        stop_btn.clicked.connect(self.stop_measurement)

        buttons_layout.addWidget(back_btn)
        buttons_layout.addWidget(stop_btn)

        header_layout.addLayout(buttons_layout)
        parent_layout.addWidget(header)

    def setup_progress_info(self, parent_layout):
        """Setup progress information section"""
        progress_widget = QWidget()
        progress_widget.setFixedHeight(140)
        progress_widget.setStyleSheet(f"""
            QWidget {{
                background: {Styles.BACKGROUND_LIGHT};
                border-bottom: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)

        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(30, 20, 30, 20)
        progress_layout.setSpacing(15)

        # Stage info
        stage_layout = QHBoxLayout()

        self.stage_label = QLabel(f"Этап 1: {self.STAGES[0]}")
        self.stage_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
                background: transparent;
            }
        """)

        self.stage_desc = QLabel("Начало процесса измерения...")
        self.stage_desc.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 14px;
                background: transparent;
            }}
        """)

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
        if is_active:
            bar.setStyleSheet(f"""
                QWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Styles.PRIMARY}, 
                        stop:1 {Styles.PRIMARY_LIGHT});
                    border-radius: 4px;
                }}
            """)
            bar.setFixedWidth(0)
        else:
            bar.setStyleSheet(f"""
                QWidget {{
                    background: {Styles.BORDER_LIGHT};
                    border-radius: 4px;
                }}
            """)
            bar.setFixedWidth(container.width())

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
        graph_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
                background: transparent;
                padding: 5px 0;
            }
        """)
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
        file_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }
        """)

        # Кнопка выбора файла
        self.select_file_btn = QPushButton("Выбрать файл данных")
        self.select_file_btn.clicked.connect(self.select_data_file)
        self.select_file_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid {Styles.PRIMARY};
            }}
        """)

        top_row.addWidget(file_title)
        top_row.addStretch()
        top_row.addWidget(self.select_file_btn)

        # Информация о выбранном файле
        self.file_info_label = QLabel("Файл не выбран")
        self.file_info_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 12px;
                background: transparent;
            }}
        """)
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
        separator.setStyleSheet(f"background: {Styles.BORDER_LIGHT};")
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
        self.status_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
                text-align: center;
                background: transparent;
            }
        """)
        self.status_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status description
        self.status_desc = QLabel("Пожалуйста, ожидайте завершения процесса.")
        self.status_desc.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 14px;
                text-align: center;
                background: transparent;
            }}
        """)
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
        sample_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                margin-bottom: 5px;
            }
        """)

        # Input field
        self.sample_name_input = QLineEdit()
        self.sample_name_input.setPlaceholderText("Введите имя образца")
        self.sample_name_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 6px;
                padding: 12px;
                color: white;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {Styles.PRIMARY};
            }}
        """)
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
        self.continue_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.PRIMARY}, stop:1 {Styles.PRIMARY_LIGHT});
                color: white;
                border: none;
                padding: 14px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                transition: all 0.2s ease;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.PRIMARY_DARK}, stop:1 {Styles.PRIMARY});
                transform: scale(1.02);
            }}
            QPushButton:disabled {{
                background: {Styles.BORDER_LIGHT};
                color: {Styles.TEXT_DISABLED};
            }}
        """)
        self.continue_btn.clicked.connect(self.add_sample)
        self.continue_btn.setEnabled(False)
        self.continue_btn.setFixedHeight(50)

        # Finish button
        self.finish_btn = QPushButton("Завершить исследование")
        self.finish_btn.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid {Styles.BORDER_MEDIUM};
                padding: 14px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                transition: all 0.2s ease;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid {Styles.PRIMARY};
            }}
            QPushButton:disabled {{
                background: {Styles.BORDER_LIGHT};
                color: {Styles.TEXT_DISABLED};
                border: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)
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
        info_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
                background: transparent;
            }
        """)
        panel_layout.addWidget(info_title)

        # Scrollable info content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

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
        print(f"Starting measurement for method: {self.method_id}")

        # Устанавливаем заголовок с методом
        method_names = {
            1: "ФРЧ", 2: "ФРД", 3: "СО",
            4: "СВЧФ1", 5: "ЩР", 6: "СВЧФ2"
        }
        method_name = method_names.get(self.method_id, f"Метод {self.method_id}")

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
                    # Переходим к следующему этапу
                    self.current_stage += 1

                    if self.current_stage < len(self.STAGES):
                        # Активируем следующий этап
                        self.update_stage_info()

                        # Если достигли этапа добавления образца
                        if self.current_stage == 3:  # "Ожидание образца"
                            self.wait_for_sample()
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
        instruction.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 14px;
                background: transparent;
                padding: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }}
        """)
        instruction.setWordWrap(True)

        self.info_layout.addWidget(instruction)

    def sample_installed(self):
        """Образец установлен - продолжаем измерение"""
        self.waiting_for_sample = False

        # Скрываем инструкцию если есть info_layout
        if hasattr(self, 'info_layout') and self.info_layout:
            for i in reversed(range(self.info_layout.count())):
                item = self.info_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()

        # Возобновляем таймер прогресса
        if hasattr(self, 'progress_timer'):
            self.progress_timer.start(500)

        # Активируем поле ввода имени образца
        if hasattr(self, 'sample_name_input'):
            self.sample_name_input.setEnabled(True)
            self.sample_name_input.setPlaceholderText("Введите имя образца")

        # Обновляем кнопку
        if hasattr(self, 'continue_btn'):
            self.continue_btn.setText("Добавить образец")

            # Отключаем старые соединения
            try:
                self.continue_btn.clicked.disconnect()
            except:
                pass

            self.continue_btn.clicked.connect(self.add_sample)

        # Обновляем статус
        if hasattr(self, 'status_title'):
            self.status_title.setText("Образец установлен")

        if hasattr(self, 'status_desc'):
            self.status_desc.setText("Введите имя образца и при необходимости выберите файл данных")

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
        """Finish and save the measurement"""
        try:
            # Сохраняем результаты в бэкенд
            result_data = {
                "id_m": self.measure_id,
                "samples": self.samples_added,
                "status": "completed"
            }

            response = self.backend.query("method_end", result_data)

            if response and response.get('success', False):
                if hasattr(self, 'status_title'):
                    self.status_title.setText("Результаты сохранены")

                if hasattr(self, 'status_desc'):
                    self.status_desc.setText("Измерение успешно завершено и сохранено в базе данных.")
            else:
                if hasattr(self, 'status_title'):
                    self.status_title.setText("Ошибка сохранения")

                if hasattr(self, 'status_desc'):
                    self.status_desc.setText("Не удалось сохранить результаты. Проверьте подключение.")

            # Эмитируем сигнал завершения
            self.measurement_finished.emit()

        except Exception as e:
            print(f"Error finishing measurement: {e}")

            if hasattr(self, 'status_title'):
                self.status_title.setText("Ошибка")

            if hasattr(self, 'status_desc'):
                self.status_desc.setText(f"Ошибка при завершении измерения: {str(e)}")

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
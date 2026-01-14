"""
Measurement process widget (embedded version) with JSON support
"""

import random
import json
import os
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFrame
)

from widgets import ModernCard, LoadingSpinner, AnimatedButton
from widgets.measurement_graph import MeasurementGraphWidget
from styles import Styles


class MeasurementProcessWidget(QWidget):
    """Widget showing measurement progress (embedded version) with JSON support"""

    # Сигналы
    measurement_finished = pyqtSignal()
    measurement_stopped = pyqtSignal()

    # Этапы измерения
    STAGES = [
        "Подготовка оборудования",
        "Калибровка резонатора",
        "Измерение без образца",
        "Измерение с образцом",
        "Обработка данных",
        "Сохранение результатов"
    ]

    def __init__(self, backend, measure_id, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.measure_id = measure_id
        self.current_stage = 0
        self.samples_added = []
        self.is_active = True

        # Настройка внешнего вида
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Styles.BACKGROUND_DARK}, 
                    stop:1 {Styles.BACKGROUND_MEDIUM});
            }}
        """)

        self.setup_ui()
        self.start_measurement_process()

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
            bar.setFixedWidth(0)  # Начинаем с 0
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

        content_layout.addWidget(graph_container, 7)  # 70% ширины

        # Side panel (30% ширины)
        side_panel = self.create_side_panel()
        content_layout.addWidget(side_panel, 3)  # 30% ширины

        parent_layout.addWidget(content_widget, 1)

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
        self.continue_btn = AnimatedButton("Добавить образец")
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
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.PRIMARY_DARK}, stop:1 {Styles.PRIMARY});
            }}
            QPushButton:disabled {{
                background: {Styles.BORDER_LIGHT};
                color: {Styles.TEXT_DISABLED};
            }}
        """)
        self.continue_btn.clicked.connect(self.add_sample)
        self.continue_btn.setEnabled(False)  # Изначально отключена

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
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
            QPushButton:disabled {{
                background: {Styles.BORDER_LIGHT};
                color: {Styles.TEXT_DISABLED};
                border: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)
        self.finish_btn.clicked.connect(self.finish_measurement)
        self.finish_btn.setEnabled(False)  # Изначально отключена

        layout.addWidget(self.continue_btn)
        layout.addWidget(self.finish_btn)

        return widget

    def start_measurement_process(self):
        """Start the measurement process"""
        # Загружаем данные измерения
        self.load_measurement_data()

        # Загружаем график из JSON файла
        self.load_graph_from_json()

        # Запускаем прогресс
        self.start_progress_animation()

        # Обновляем заголовок
        if hasattr(self, 'measurement_data'):
            title = self.measurement_data.get('title', f'#{self.measure_id}')
            self.title_label.setText(f"Исследование: {title}")

    def load_measurement_data(self):
        """Load measurement data from backend"""
        try:
            self.measurement_data = self.backend.ferro_query(
                "read_data",
                {"id_m": self.measure_id}
            )
        except:
            self.measurement_data = {}

    def load_graph_from_json(self):
        """Load graph data from JSON file"""
        try:
            # Ищем JSON файлы в data_ferro
            data_dir = "data_ferro"
            if os.path.exists(data_dir):
                json_files = [f for f in os.listdir(data_dir)
                              if f.endswith('.json')]

                if json_files:
                    # Для демо берем первый попавшийся файл
                    # В реальном приложении здесь должна быть логика сопоставления
                    json_path = os.path.join(data_dir, json_files[0])

                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)

                    # Загружаем данные в график
                    if self.graph.load_data_from_json(json_data):
                        print(f"Successfully loaded JSON from {json_path}")
                        return True

            # Если JSON файл не найден, загружаем тестовые данные
            return self.load_test_data()

        except Exception as e:
            print(f"Error loading JSON: {e}")
            return self.load_test_data()

    def load_test_data(self):
        """Load test data if JSON file not found"""
        try:
            # Генерируем тестовые данные
            import numpy as np

            # Генерируем частоты
            frequencies = np.linspace(8.0, 12.0, 401)  # 8-12 ГГц

            # Базовое измерение (резонансная кривая)
            center_freq = 10.0
            q_factor = 100
            baseline = -20 - 40 * np.exp(-((frequencies - center_freq) ** 2) / (center_freq / q_factor) ** 2)

            # Создаем структуру данных
            test_data = {
                'x': [f"+{freq:.9f}E+09" for freq in frequencies],
                'y_res': [f"{amp:.6f}" for amp in baseline],
                'title': f"Тестовое измерение #{self.measure_id}",
                'description': "Тестовые данные для демонстрации",
                'date': "15052025",
                'time': "17:45",
                'method': "4",
                'y_samples': {
                    '1': {
                        'name': 'Тестовый образец 1',
                        'y_res': [f"{amp + np.random.normal(0, 0.5):.6f}" for amp in baseline],
                        'E': 9.87,
                        'tgo': 1.23e-4,
                        'AE': -44.9,
                        'fe': '+8.645000000E+09'
                    },
                    '2': {
                        'name': 'Тестовый образец 2',
                        'y_res': [f"{amp + np.random.normal(0, 0.7):.6f}" for amp in baseline],
                        'E': 3.21,
                        'tgo': 2.34e-4,
                        'AE': -43.8,
                        'fe': '+8.730000000E+09'
                    }
                }
            }

            return self.graph.load_data_from_json(test_data)

        except Exception as e:
            print(f"Error loading test data: {e}")
            return False

    def start_progress_animation(self):
        """Start the progress bar animation"""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)  # Обновляем каждые 100ms

    def update_progress(self):
        """Update progress bars and stages"""
        if not self.is_active:
            return

        # Увеличиваем прогресс текущего этапа
        current_bar = self.bars[self.current_stage]
        if current_bar:
            current_width = current_bar.width()
            parent_width = current_bar.parent().width()

            if current_width < parent_width * 0.95:  # Доводим до 95%
                increment = parent_width * 0.01  # 1% за шаг
                new_width = min(current_width + increment, parent_width * 0.95)
                current_bar.setFixedWidth(int(new_width))

                # Обновляем процент
                total_progress = sum(bar.width() for bar in self.bars if bar)
                total_width = sum(bar.parent().width() for bar in self.bars)
                percent = int((total_progress / total_width) * 100)
                self.progress_percent.setText(f"{percent}%")

            else:
                # Переходим к следующему этапу
                self.current_stage += 1

                if self.current_stage < len(self.STAGES):
                    # Активируем следующий этап
                    self.update_stage_info()

                    # Если достигли этапа добавления образца
                    if self.current_stage == 3:  # "Измерение с образцом"
                        self.enable_sample_input()
                else:
                    # Все этапы завершены
                    self.complete_measurement()

        # Периодически обновляем график
        if random.random() < 0.05:  # 5% шанс обновить
            self.update_live_graph()

    def update_stage_info(self):
        """Update stage information display"""
        if self.current_stage < len(self.STAGES):
            self.stage_label.setText(f"Этап {self.current_stage + 1}: {self.STAGES[self.current_stage]}")

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
                self.stage_desc.setText(descriptions[self.current_stage])

    def enable_sample_input(self):
        """Enable sample input section"""
        self.continue_btn.setEnabled(True)
        self.sample_name_input.setEnabled(True)

        self.status_title.setText("Ожидание образца")
        self.status_desc.setText("Поместите образец в резонатор и введите имя образца.")

        # Останавливаем анимацию спиннера
        self.loading_spinner.hide()

    def update_live_graph(self):
        """Update graph with simulated live data"""
        # В реальном приложении здесь будет обновление данных с оборудования
        # Для демо просто обновляем отображение
        pass

    def add_sample(self):
        """Add a sample to the measurement"""
        sample_name = self.sample_name_input.text().strip()

        if not sample_name:
            # Генерируем имя по умолчанию
            sample_num = len(self.samples_added) + 1
            sample_name = f"Образец {sample_num}"

        # Добавляем в список
        self.samples_added.append(sample_name)

        # Обновляем статус
        self.status_title.setText("Образец добавлен")
        self.status_desc.setText(f"Образец '{sample_name}' добавлен к измерению.")

        # Очищаем поле ввода
        self.sample_name_input.clear()

        # Обновляем прогресс
        if self.current_stage == 3:  # На этапе добавления образцов
            samples_needed = 3  # Например, нужно 3 образца
            progress_per_sample = (self.bars[3].parent().width() * 0.95) / samples_needed

            if len(self.samples_added) <= samples_needed:
                # Увеличиваем прогресс этапа
                current_bar = self.bars[3]
                new_width = min(
                    current_bar.width() + progress_per_sample,
                    current_bar.parent().width() * 0.95
                )
                current_bar.setFixedWidth(int(new_width))

            if len(self.samples_added) >= samples_needed:
                # Все образцы добавлены
                self.continue_btn.setEnabled(False)
                self.finish_btn.setEnabled(True)
                self.status_desc.setText("Все образцы добавлены. Можно завершить исследование.")

    def complete_measurement(self):
        """Complete the measurement process"""
        self.is_active = False
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

        self.status_title.setText("Исследование завершено")
        self.status_desc.setText("Все этапы измерения успешно выполнены.")

        self.finish_btn.setEnabled(True)
        self.continue_btn.setEnabled(False)
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

            response = self.backend.ferro_query("method_end", result_data)

            if response and response.get('success', False):
                self.status_title.setText("Результаты сохранены")
                self.status_desc.setText("Измерение успешно завершено и сохранено в базе данных.")
            else:
                self.status_title.setText("Ошибка сохранения")
                self.status_desc.setText("Не удалось сохранить результаты. Проверьте подключение.")

            # Эмитируем сигнал завершения
            self.measurement_finished.emit()

        except Exception as e:
            print(f"Error finishing measurement: {e}")
            self.status_title.setText("Ошибка")
            self.status_desc.setText(f"Ошибка при завершении измерения: {str(e)}")

    def stop_measurement(self):
        """Stop the measurement process"""
        self.is_active = False

        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

        self.status_title.setText("Исследование остановлено")
        self.status_desc.setText("Процесс измерения был прерван пользователем.")

        # Отключаем кнопки
        self.continue_btn.setEnabled(False)
        self.finish_btn.setEnabled(False)
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
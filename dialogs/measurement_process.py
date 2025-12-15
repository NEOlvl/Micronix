"""
Measurement process dialog
"""

import random
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget,
                            QLabel, QPushButton, QLineEdit)
from widgets import ModernCard, LoadingSpinner, AnimatedButton, MeasurementGraphWidget


class MeasurementProcessDialog(QDialog):
    """Dialog showing measurement progress"""

    def __init__(self, backend, measure_id, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.measure_id = measure_id
        self.current_stage = 1
        self.setStyleSheet("""
            MeasurementProcessDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #222326, stop:1 #191a1d);
            }
        """)
        self.setup_ui()
        self.start_measurement_process()

    def setup_ui(self):
        self.setWindowTitle("Исследование в процессе")
        self.setModal(True)
        self.setFixedSize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.title_label = QLabel("Исследование #...")
        self.title_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600; background: transparent;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        stop_btn = QPushButton("Остановить исследование")
        stop_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.4);
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
        stop_btn.clicked.connect(self.reject)
        header_layout.addWidget(stop_btn)

        layout.addWidget(header)

        # Progress info
        progress_widget = QWidget()
        progress_widget.setFixedHeight(120)
        progress_widget.setStyleSheet("""
            QWidget {
                background: rgba(40, 41, 44, 0.7);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(30, 20, 30, 20)

        # Stage info
        stage_layout = QHBoxLayout()
        self.stage_label = QLabel("Этап 1")
        self.stage_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600; background: transparent;")

        self.stage_desc = QLabel("Подготовка оборудования...")
        self.stage_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px; background: transparent;")

        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet("color: white; font-size: 24px; font-weight: 600; background: transparent;")

        stage_layout.addWidget(self.stage_label)
        stage_layout.addWidget(self.stage_desc)
        stage_layout.addStretch()
        stage_layout.addWidget(self.progress_label)

        progress_layout.addLayout(stage_layout)

        # Progress bars
        bars_layout = QHBoxLayout()
        self.bars = []
        widths = [10, 20, 50, 20]  # Percentage widths for each stage

        for i, width in enumerate(widths):
            bar_container = QWidget()
            bar_container.setFixedHeight(8)
            bar_container.setStyleSheet("background: rgba(255, 255, 255, 0.1); border-radius: 4px;")

            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(2, 0, 2, 0)

            progress_bar = QWidget()
            progress_bar.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7879F1, stop:1 #9A9BFF); border-radius: 3px;")
            progress_bar.setFixedWidth(0)

            bar_layout.addWidget(progress_bar)
            bars_layout.addWidget(bar_container)
            self.bars.append(progress_bar)

        progress_layout.addLayout(bars_layout)
        layout.addWidget(progress_widget)

        # Graph area
        graph_widget = QWidget()
        graph_layout = QHBoxLayout(graph_widget)
        graph_layout.setContentsMargins(20, 20, 20, 20)
        graph_layout.setSpacing(20)

        # Main graph
        self.graph = MeasurementGraphWidget()
        self.graph.plot_widget.setBackground('#1a1b1e')
        graph_layout.addWidget(self.graph, 3)

        # Side info
        side_info = ModernCard()
        side_info.setFixedWidth(300)
        side_layout = QVBoxLayout(side_info)
        side_layout.setContentsMargins(20, 20, 20, 20)

        # Loading animation
        self.loading_spinner = LoadingSpinner()
        side_layout.addWidget(self.loading_spinner, 0, Qt.AlignmentFlag.AlignHCenter)

        self.status_title = QLabel("Исследование в процессе")
        self.status_title.setStyleSheet("color: white; font-size: 16px; font-weight: 600; text-align: center; background: transparent;")
        self.status_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_desc = QLabel("Пожалуйста, ожидайте завершения процесса.")
        self.status_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px; text-align: center; background: transparent;")
        self.status_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_desc.setWordWrap(True)

        side_layout.addWidget(self.status_title)
        side_layout.addWidget(self.status_desc)
        side_layout.addStretch()

        # Sample input (will be shown later)
        self.sample_input_container = QWidget()
        self.sample_input_container.hide()
        sample_layout = QVBoxLayout(self.sample_input_container)

        sample_label = QLabel("Имя образца:")
        sample_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")

        self.sample_name_input = QLineEdit()
        self.sample_name_input.setPlaceholderText("Введите имя образца")
        self.sample_name_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
        """)

        continue_btn = AnimatedButton("Продолжить")
        continue_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: 600;
                margin-top: 10px;
            }
        """)
        continue_btn.clicked.connect(self.add_sample)

        end_btn = QPushButton("Завершить исследование")
        end_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 12px;
                border-radius: 6px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        end_btn.clicked.connect(self.finish_measurement)

        sample_layout.addWidget(sample_label)
        sample_layout.addWidget(self.sample_name_input)
        sample_layout.addWidget(continue_btn)
        sample_layout.addWidget(end_btn)

        side_layout.addWidget(self.sample_input_container)
        graph_layout.addWidget(side_info)

        layout.addWidget(graph_widget, 1)

    def start_measurement_process(self):
        """Start the measurement process with animations"""
        # Update title
        measure_data = self.backend.ferro_query("read_data", {"id_m": self.measure_id})
        self.title_label.setText(f"Исследование #{measure_data.get('title', '...')}")

        # Start stage progression
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)

        # Load graph data
        self.load_graph_data()

    def update_progress(self):
        """Update progress bars and stages"""
        if self.current_stage == 1:
            progress = self.bars[0].width() + 1
            max_width = int(self.bars[0].parent().width() * 0.96)  # 96% of container
            if progress < max_width:
                self.bars[0].setFixedWidth(progress)
                self.progress_label.setText(f"{int(progress / max_width * 100)}%")
            else:
                self.current_stage = 2
                self.stage_label.setText("Этап 2")
                self.stage_desc.setText("Снятие данных с рефлектометра")

        elif self.current_stage == 2:
            progress = self.bars[1].width() + 2
            max_width = int(self.bars[1].parent().width() * 0.96)
            if progress < max_width:
                self.bars[1].setFixedWidth(progress)
                self.progress_label.setText(f"{int(progress / max_width * 100)}%")
            else:
                self.current_stage = 3
                # Show sample input
                self.loading_spinner.hide()
                self.status_title.setText("Ожидание образца")
                self.status_desc.setText("Поместите образец в резонатор, затем нажмите продолжить.")
                self.sample_input_container.show()

        # Update graph periodically
        if random.random() < 0.1:  # 10% chance each tick
            self.update_live_graph()

    def load_graph_data(self):
        """Load initial graph data"""
        x_data = self.backend.ferro_query("create_graph_x", 0)
        y_data = self.backend.ferro_query("create_graph", 0)

        self.graph.plot_data(x_data, y_data, '#7879F1', 2, "Без образца")

    def update_live_graph(self):
        """Update graph with live data"""
        # Simulate live data updates
        if hasattr(self, 'live_data_counter'):
            self.live_data_counter += 1
        else:
            self.live_data_counter = 0

        # Add some random variation to simulate live data
        if self.live_data_counter % 10 == 0:
            y_data = self.backend.ferro_query("create_graph", 0)
            noise = np.random.normal(0, 0.1, len(y_data))
            y_data_live = [y + n for y, n in zip(y_data, noise)]

            # Update plot
            self.graph.plot_widget.clear()
            x_data = self.backend.ferro_query("create_graph_x", 0)
            self.graph.plot_data(x_data, y_data_live, '#7879F1', 2, "Без образца")

    def add_sample(self):
        """Add sample to measurement"""
        sample_name = self.sample_name_input.text().strip()
        if not sample_name:
            sample_name = f"Sample-{random.randint(1000, 9999)}"

        # Call backend to add sample
        data_obj = {
            "id_m": self.measure_id,
            "new_sample_name": sample_name
        }
        response = self.backend.ferro_query("new_sample", data_obj)

        # Update graph with sample data
        measure_data = self.backend.ferro_query("read_data", {"id_m": self.measure_id})
        if measure_data['y_samples']:
            sample = list(measure_data['y_samples'].values())[-1]  # Get latest sample
            self.graph.plot_data(measure_data['x'], sample['y_res'], '#f8c33c', 2, sample_name)

        # Reset for next sample
        self.sample_name_input.clear()
        self.status_title.setText("Ожидание образца")
        self.status_desc.setText(
            "Поместите новый образец в резонатор, затем нажмите продолжить или завершите исследование.")

        # Update progress bar
        progress = self.bars[2].width() + 25
        max_width = int(self.bars[2].parent().width() * 0.96)
        if progress < max_width:
            self.bars[2].setFixedWidth(progress)
        else:
            self.bars[3].setFixedWidth(self.bars[3].parent().width() * 0.96)

    def finish_measurement(self):
        """Finish measurement process"""
        data_obj = {"id_m": self.measure_id}
        response = self.backend.ferro_query("method_end", data_obj)
        self.accept()
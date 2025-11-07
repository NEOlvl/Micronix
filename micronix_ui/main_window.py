from PyQt6.QtWidgets import (
    QMainWindow,
    QAction,
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QProgressBar,
)
from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot
from micronix_core.math import compute_example
import time


class WorkerSignals(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    result = pyqtSignal(object)


class Worker(QRunnable):
    """
    Простой QRunnable-воркер с сигналами.
    Используется для долгих вычислений, чтобы не блокировать GUI.
    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        # Здесь запускается функция в пуле потоков
        try:
            for i in range(5):
                time.sleep(0.1)  # демонстрация прогресса
                self.signals.progress.emit(int((i + 1) * 20))
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            result = e
        self.signals.result.emit(result)
        self.signals.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Micronix (PyQt6) — skeleton")
        self.resize(800, 600)

        # Thread pool для фоновой работы
        self.pool = QThreadPool.globalInstance()

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Кнопки (пока минимальные)
        self.load_btn = QPushButton("Загрузить данные")
        self.run_btn = QPushButton("Запустить расчёт")
        self.progress = QProgressBar()
        self.status_label = QLabel("Готов")

        layout.addWidget(self.load_btn)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        load_action = QAction("Открыть...", self)
        load_action.triggered.connect(self.on_load)
        file_menu.addAction(load_action)

        # Сигналы
        self.load_btn.clicked.connect(self.on_load)
        self.run_btn.clicked.connect(self.on_run)

    def on_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл данных", "", "All Files (*)")
        if path:
            self.status_label.setText(f"Загружен: {path}")
            # TODO: добавить парсер/обработчик данных

    def on_run(self):
        self.status_label.setText("Запущено")
        self.progress.setValue(0)
        # Запускаем демонстрационную задачу в фоне
        worker = Worker(self._long_computation, 42)
        worker.signals.progress.connect(self.progress.setValue)
        worker.signals.result.connect(self.on_result)
        worker.signals.finished.connect(lambda: self.status_label.setText("Готов"))
        self.pool.start(worker)

    def _long_computation(self, value):
        # Пример вычисления, позже заменим на реальные функции проекта
        return compute_example(value)

    def on_result(self, result):
        self.status_label.setText(f"Результат: {result}")
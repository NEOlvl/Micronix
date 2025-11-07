from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QProgressBar,
    QTableView,
    QSplitter,
    QHBoxLayout,
    QStatusBar,
)
from PyQt6.QtGui import QAction, QStandardItemModel, QStandardItem
from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot, Qt
import pyqtgraph as pg
from micronix_core.math import compute_example
import time
import traceback


class WorkerSignals(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    result = pyqtSignal(object)
    error = pyqtSignal(str)


class Worker(QRunnable):
    """
    Общий воркер. fn должен вернуть результат или поднять исключение.
    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            # пример прогресса (можно удалить внутри конкретной функции)
            self.signals.progress.emit(5)
            result = self.fn(*self.args, **self.kwargs)
            self.signals.progress.emit(100)
            self.signals.result.emit(result)
        except Exception:
            tb = traceback.format_exc()
            self.signals.error.emit(tb)
        finally:
            self.signals.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Micronix (PyQt6) — skeleton")
        self.resize(1000, 700)

        # Thread pool для фоновой работы
        self.pool = QThreadPool.globalInstance()

        # Центральный виджет: Splitter (таблица | график)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        controls_layout = QHBoxLayout()
        self.load_btn = QPushButton("Загрузить данные")
        self.run_btn = QPushButton("Запустить расчёт")
        controls_layout.addWidget(self.load_btn)
        controls_layout.addWidget(self.run_btn)
        main_layout.addLayout(controls_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # Левый: таблица
        self.table = QTableView()
        self.model = QStandardItemModel(0, 0)
        self.table.setModel(self.model)
        self.splitter.addWidget(self.table)

        # Правый: график (pyqtgraph)
        self.plot_widget = pg.PlotWidget(title="График данных")
        self.plot = self.plot_widget.plot([], [])
        self.splitter.addWidget(self.plot_widget)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        # Статусбар и прогресс
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.status.addPermanentWidget(self.progress)
        self.status_label = QLabel("Готов")
        self.status.addWidget(self.status_label)

        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        load_action = QAction("Открыть...", self)
        load_action.triggered.connect(self.on_load)
        file_menu.addAction(load_action)

        # Сигналы
        self.load_btn.clicked.connect(self.on_load)
        self.run_btn.clicked.connect(self.on_run)

        # Хранилище данных
        self.current_data = None  # list[list[float]] или None

    def on_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл данных", "", "All Files (*)")
        if not path:
            return
        self.status_label.setText(f"Загружаем: {path}")
        # Запускаем чтение файла в фоне
        worker = Worker(self._load_file, path)
        worker.signals.progress.connect(self.progress.setValue)
        worker.signals.result.connect(self._on_loaded)
        worker.signals.error.connect(self._on_error)
        worker.signals.finished.connect(lambda: self.status_label.setText("Готов"))
        self.pool.start(worker)

    def _load_file(self, path):
        """
        Простой парсер: пытается считать файл как таблицу чисел,
        разделитель — пробел/таб/запятая.
        Возвращает список строк: [[v1, v2, ...], ...]
        """
        data = []
        total_lines = 0
        # узнаем количество строк для прогресса (необязательно)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in f:
                total_lines += 1
        if total_lines == 0:
            return data
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # нормализуем разделители
                line = line.replace(",", " ").replace("\t", " ")
                parts = [p for p in line.split(" ") if p != ""]
                # преобразуем в числа, если возможно
                row = []
                for p in parts:
                    try:
                        row.append(float(p))
                    except ValueError:
                        row.append(p)  # оставим как строку
                data.append(row)
                # обновление прогресса (примерно)
                if total_lines:
                    self.progress.setValue(int((i + 1) / total_lines * 90))
        return data

    def _on_loaded(self, data):
        # Сохранить и отобразить
        self.current_data = data
        self._populate_table(data)
        self._plot_default(data)
        self.progress.setValue(100)
        self.status_label.setText(f"Загружено: {len(data)} строк")

    def _on_error(self, tb):
        self.status_label.setText("Ошибка при загрузке")
        print(tb)

    def _populate_table(self, data):
        # адаптивно установим кол-во колонок
        cols = max((len(r) for r in data), default=0)
        self.model = QStandardItemModel(len(data), cols)
        for r, row in enumerate(data):
            for c in range(cols):
                v = row[c] if c < len(row) else ""
                item = QStandardItem(str(v))
                self.model.setItem(r, c, item)
        self.table.setModel(self.model)
        # можно дополнительно установить заголовки

    def _plot_default(self, data):
        # Если данные числовые — строим график по первой колонке
        if not data:
            self.plot.setData([], [])
            return
        # выбираем только числовые значения из колонки 0
        xs = []
        ys = []
        for i, row in enumerate(data):
            if len(row) == 0:
                continue
            try:
                y = float(row[0])
                xs.append(i)
                ys.append(y)
            except Exception:
                continue
        self.plot.setData(xs, ys, pen=pg.mkPen("b", width=1))
        self.plot_widget.autoRange()

    def on_run(self):
        # Запуск вычислений — пример запуска compute_example на числах из первой колонки
        if not self.current_data:
            self.status_label.setText("Нет данных для расчёта")
            return
        self.status_label.setText("Вычисления...")
        worker = Worker(self._compute_on_data, self.current_data)
        worker.signals.progress.connect(self.progress.setValue)
        worker.signals.result.connect(self._on_compute_result)
        worker.signals.error.connect(self._on_error)
        worker.signals.finished.connect(lambda: self.status_label.setText("Готов"))
        self.pool.start(worker)

    def _compute_on_data(self, data):
        # пример: применить compute_example к каждой числовой записи первой колонки
        results = []
        for i, row in enumerate(data):
            try:
                v = float(row[0])
            except Exception:
                continue
            # имитируем тяжёлую операцию
            time.sleep(0.01)
            results.append(compute_example(v))
            if i % 10 == 0:
                # отправим промежуточный прогресс
                self.progress.setValue(int(i / max(len(data), 1) * 80))
        return results

    def _on_compute_result(self, results):
        # показать результат: простой график
        if not results:
            self.status_label.setText("Результат пуст")
            return
        xs = list(range(len(results)))
        self.plot.setData(xs, results, pen=pg.mkPen("r", width=1))
        self.status_label.setText(f"Вычислено: {len(results)} значений")
        self.progress.setValue(100)
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt


# ---------------- Sidebar ----------------
class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setObjectName("Sidebar")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("FERRO")
        title.setObjectName("SidebarTitle")

        layout.addWidget(title)
        layout.addSpacing(20)

        for text in ["Главная", "Измерения", "Отчёты"]:
            btn = QPushButton(text)
            btn.setObjectName("SidebarButton")
            layout.addWidget(btn)

        layout.addStretch()


# ---------------- Top bar ----------------
class TopBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(56)
        self.setObjectName("TopBar")

        layout = QHBoxLayout(self)

        search = QLineEdit()
        search.setPlaceholderText("Бином")
        search.setObjectName("SearchField")

        layout.addWidget(search)


# ---------------- Method card ------------
class MethodCard(QFrame):
    def __init__(self, title, desc):
        super().__init__()
        self.setObjectName("MethodCard")
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)

        t = QLabel(title)
        t.setObjectName("CardTitle")

        d = QLabel(desc)
        d.setWordWrap(True)

        layout.addWidget(t)
        layout.addWidget(d)
        layout.addStretch()


# ---------------- Research card ----------
class ResearchCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("ResearchCard")

        layout = QHBoxLayout(self)

        graph = QLabel("📈 график")
        graph.setFixedSize(160, 90)
        graph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph.setStyleSheet("border:1px dashed #444;")

        info = QLabel(
            "<b>Метод объёмного резонатора</b><br>"
            "Добротность (Q): 789<br>"
            "Тангенс потерь: 0.002"
        )

        layout.addWidget(graph)
        layout.addWidget(info)
        layout.addStretch()


# ---------------- Home page --------------
class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setSpacing(24)

        title = QLabel("Главная")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # ---- Methods ----
        methods_layout = QHBoxLayout()
        methods_layout.setSpacing(16)

        methods_layout.addWidget(MethodCard(
            "Метод 1",
            "Метод объёмного резонатора при фиксированной резонансной частоте"
        ))
        methods_layout.addWidget(MethodCard(
            "Метод 2",
            "Метод объёмного резонатора при фиксированной резонансной длине"
        ))
        methods_layout.addWidget(MethodCard(
            "Метод 3",
            "Метод объёмного резонатора для СВЧ ферритов"
        ))

        root.addLayout(methods_layout)

        # ---- Recent ----
        recent = QLabel("Последние исследования")
        recent.setObjectName("SectionTitle")
        root.addWidget(recent)

        for _ in range(3):
            root.addWidget(ResearchCard())

        root.addStretch()


# ---------------- Main window ------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FERRO")
        self.resize(1200, 800)

        central = QWidget()
        main_layout = QHBoxLayout(central)

        sidebar = Sidebar()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        topbar = TopBar()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        page = HomePage()
        scroll.setWidget(page)

        content_layout.addWidget(topbar)
        content_layout.addWidget(scroll)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.setCentralWidget(central)


# ---------------- Run app ----------------
app = QApplication(sys.argv)

app.setStyleSheet("""
* {
    font-family: Segoe UI;
    color: #e6e6e6;
}

QMainWindow {
    background: #23252b;
}

#Sidebar {
    background: #1c1e24;
}

#SidebarTitle {
    font-size: 20px;
    font-weight: bold;
}

#SidebarButton {
    background: transparent;
    text-align: left;
    padding: 8px 12px;
    border-radius: 6px;
}

#SidebarButton:hover {
    background: #2a2d35;
}

#TopBar {
    background: #2a2d35;
}

#SearchField {
    background: #1c1e24;
    border-radius: 6px;
    padding: 6px 10px;
}

#PageTitle {
    font-size: 26px;
    font-weight: bold;
}

#SectionTitle {
    font-size: 16px;
    opacity: 0.7;
}

#MethodCard, #ResearchCard {
    background: #2b2d33;
    border-radius: 12px;
    padding: 12px;
}

QWidget {
    background: #23252b;
}
""")

window = MainWindow()
window.show()

sys.exit(app.exec())

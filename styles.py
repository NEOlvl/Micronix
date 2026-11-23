"""
Common styles and style utilities.

Единая точка темы оформления (pyqt6-ui-development-rules):
вся QSS применяется один раз на уровне QApplication через
apply_theme(). Виджеты получают вид через динамические
свойства и objectName, а не через разрозненные setStyleSheet:

    btn.setProperty("btnStyle", "primary")   # варианты кнопок
    lbl.setProperty("role", "h1")            # роли текстов
    card.setProperty("selected", True)       # состояние карточек
    w.setObjectName("pageHeader")            # именованные панели
"""

from string import Template


class Styles:
    """Common style definitions"""

    # Основная фиолетовая палитра
    PRIMARY = "#7879F1"  # Основной фиолетовый
    PRIMARY_LIGHT = "#9A9BFF"  # Светлый фиолетовый
    PRIMARY_DARK = "#5A5BD1"  # Темный фиолетовый

    # Дополнительные оттенки фиолетового
    VIOLET = "#9D7BF1"  # Яркий фиолетовый
    LAVENDER = "#B19BFF"  # Лавандовый
    LILAC = "#C7BBFF"  # Сиреневый

    # Фоны и границы
    BACKGROUND_DARK = "#1a1b1e"
    BACKGROUND_MEDIUM = "#222326"
    BACKGROUND_LIGHT = "#25262a"

    # Текст
    TEXT_PRIMARY = "white"
    TEXT_SECONDARY = "rgba(255, 255, 255, 0.7)"
    TEXT_DISABLED = "rgba(255, 255, 255, 0.5)"

    # Границы
    BORDER_LIGHT = "rgba(255, 255, 255, 0.1)"
    BORDER_MEDIUM = "rgba(255, 255, 255, 0.2)"

    # Градиенты
    @staticmethod
    def primary_gradient():
        return "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7879F1, stop:1 #9A9BFF)"

    @staticmethod
    def violet_gradient():
        return "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9D7BF1, stop:1 #B19BFF)"

    @staticmethod
    def card_background():
        return """
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.1),
                stop:1 rgba(255, 255, 255, 0.05));
        """

    # Стили как свойства класса (не статические)
    CARD = f"""
        {card_background.__func__()}
        border: 1px solid {BORDER_LIGHT};
        border-radius: 12px;
    """

    BUTTON_PRIMARY = f"""
        QPushButton {{
            background: {primary_gradient.__func__()};
            color: {TEXT_PRIMARY};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6A6BE1, stop:1 #8A8BEF);
        }}
    """

    INPUT_FIELD = f"""
        QLineEdit, QSpinBox, QComboBox {{
            background: rgba(40, 41, 44, 0.9);
            border: 1px solid {BORDER_MEDIUM};
            border-radius: 6px;
            padding: 8px 12px;
            color: {TEXT_PRIMARY};
            selection-background-color: rgba(120, 121, 241, 0.5);
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid rgba(120, 121, 241, 0.6);
        }}
    """

    # Фабричные методы
    @staticmethod
    def create_card_style(background=None, border=None):
        """Create card style with optional overrides"""
        style = Styles.CARD
        if background:
            style = style.replace(Styles.card_background(), f"background: {background};")
        if border:
            style = style.replace(f"border: 1px solid {Styles.BORDER_LIGHT};",
                                  f"border: 1px solid {border};")
        return style


# Создаем синонимы для обратной совместимости
CARD = Styles.CARD
BUTTON_PRIMARY = Styles.BUTTON_PRIMARY
INPUT_FIELD = Styles.INPUT_FIELD


# ------------------------------------------------------------------
# Design tokens (единый источник — подставляются в APP_QSS)
# ------------------------------------------------------------------
_TOKENS = {
    # Акцент
    'primary': Styles.PRIMARY,
    'primary_light': Styles.PRIMARY_LIGHT,
    'primary_dark': Styles.PRIMARY_DARK,
    # Поверхности
    'bg_app': Styles.BACKGROUND_DARK,        # фон приложения
    'bg_panel': Styles.BACKGROUND_MEDIUM,    # хедеры/панели
    'bg_sidebar': '#1d1e22',                 # сайдбар
    'bg_card': '#242529',                    # карточки
    'bg_card_hover': '#2a2b31',
    'bg_input': '#26272c',                   # поля ввода
    'bg_button': '#2e2f35',                  # кнопки по умолчанию
    'bg_button_hover': '#383940',
    # Текст
    'text': '#ffffff',
    'text_secondary': 'rgba(255, 255, 255, 0.65)',
    'text_disabled': 'rgba(255, 255, 255, 0.35)',
    # Границы
    'border': 'rgba(255, 255, 255, 0.09)',
    'border_hover': 'rgba(255, 255, 255, 0.18)',
    # Семантика
    'danger': '#EF4444',
    'danger_text': '#FF7B7B',
    'success': '#4CAF50',
}

_QSS = Template(r"""
/* ==================== База ==================== */
QWidget {
    color: $text;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog, QMessageBox {
    background: $bg_app;
}
QLabel {
    background: transparent;
}
QLabel:disabled {
    color: $text_disabled;
}

/* ==================== Кнопки ==================== */
QPushButton {
    background: $bg_button;
    color: $text;
    border: 1px solid $border_hover;
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background: $bg_button_hover;
    border-color: rgba(255, 255, 255, 0.28);
}
QPushButton:pressed {
    background: #222329;
}
QPushButton:disabled {
    background: #232428;
    color: $text_disabled;
    border-color: $border;
}

QPushButton[btnStyle="primary"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $primary, stop:1 $primary_light);
    border: none;
    font-weight: 600;
}
QPushButton[btnStyle="primary"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6A6BE1, stop:1 #8A8BEF);
}
QPushButton[btnStyle="primary"]:pressed {
    background: $primary_dark;
}
QPushButton[btnStyle="primary"]:disabled {
    background: rgba(255, 255, 255, 0.08);
    color: $text_disabled;
}

QPushButton[btnStyle="secondary"] {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid $border_hover;
}
QPushButton[btnStyle="secondary"]:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: $primary;
}

QPushButton[btnStyle="danger"] {
    background: rgba(239, 68, 68, 0.18);
    border: 1px solid rgba(239, 68, 68, 0.45);
    color: $text;
}
QPushButton[btnStyle="danger"]:hover {
    background: rgba(239, 68, 68, 0.28);
}

QPushButton[btnStyle="link"] {
    background: transparent;
    border: none;
    color: $primary_light;
    padding: 0;
    font-weight: 600;
}
QPushButton[btnStyle="link"]:hover {
    color: $primary;
    text-decoration: underline;
}

QPushButton[btnStyle="nav"] {
    background: transparent;
    border: none;
    border-radius: 10px;
    text-align: left;
    padding: 0 14px;
    color: $text_secondary;
    font-size: 14px;
    font-weight: 500;
}
QPushButton[btnStyle="nav"]:hover {
    background: rgba(255, 255, 255, 0.05);
    color: $text;
}
QPushButton[btnStyle="nav"][active="true"] {
    background: $primary;
    color: $text;
    font-weight: 600;
}

QPushButton[btnStyle="navSub"] {
    background: transparent;
    border: none;
    border-radius: 0;
    text-align: left;
    padding: 10px 30px;
    color: $text_secondary;
    font-size: 14px;
}
QPushButton[btnStyle="navSub"]:hover {
    background: rgba(255, 255, 255, 0.05);
    color: $text;
}

/* ==================== Поля ввода ==================== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background: $bg_input;
    border: 1px solid $border_hover;
    border-radius: 7px;
    padding: 8px 12px;
    color: $text;
    selection-background-color: rgba(120, 121, 241, 0.5);
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid $primary;
}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
    background: #212225;
    color: $text_disabled;
}
QLineEdit::placeholder {
    color: $text_disabled;
}

QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background: #2b2c31;
    color: $text;
    border: 1px solid $border_hover;
    selection-background-color: $primary;
    outline: none;
}

/* ==================== Группы ==================== */
QGroupBox {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid $border_hover;
    border-radius: 10px;
    margin-top: 22px;
    padding: 16px 14px 12px 14px;
    font-size: 14px;
    font-weight: 600;
    color: $text;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: $text;
}

/* ==================== Таблицы ==================== */
QTableWidget {
    background: #1e1f23;
    color: $text;
    border: 1px solid $border;
    border-radius: 8px;
    gridline-color: rgba(255, 255, 255, 0.06);
    alternate-background-color: rgba(255, 255, 255, 0.03);
    selection-background-color: rgba(120, 121, 241, 0.35);
}
QTableWidget::item {
    padding: 6px 10px;
}
QTableWidget::item:selected {
    background: rgba(120, 121, 241, 0.35);
}
QHeaderView::section {
    background: #26272c;
    color: $text_secondary;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid $border;
    font-weight: 600;
}
QTableCornerButton::section {
    background: #26272c;
}

/* ==================== Прочие контролы ==================== */
QCheckBox, QRadioButton {
    color: $text;
    spacing: 10px;
    background: transparent;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 17px;
    height: 17px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    background: $bg_input;
}
QCheckBox::indicator {
    border-radius: 4px;
}
QRadioButton::indicator {
    border-radius: 9px;
}
QCheckBox::indicator:checked {
    background: $primary;
    border-color: $primary;
}
QRadioButton::indicator:checked {
    background: $primary;
    border-color: $primary;
}

QProgressBar {
    background: $bg_input;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: $text;
    min-height: 8px;
    max-height: 8px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $primary, stop:1 $primary_light);
    border-radius: 4px;
}

/* ==================== Скролл ==================== */
QScrollArea, QAbstractScrollArea {
    background: transparent;
    border: none;
}
/* viewport и контент-виджет QScrollArea не должны
   рисовать дефолтный светлый фон палитры */
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollArea > QWidget > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.3);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(255, 255, 255, 0.3);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QSplitter::handle {
    background: rgba(255, 255, 255, 0.08);
}
QSplitter::handle:hover {
    background: rgba(120, 121, 241, 0.35);
}

QToolTip {
    background: #2e2f34;
    color: $text;
    border: 1px solid $border_hover;
    padding: 6px 8px;
}

/* ==================== Карточки ==================== */
ModernCard, MethodCard {
    background: $bg_card;
    border: 1px solid $border;
    border-radius: 12px;
}
MethodCard:hover {
    background: $bg_card_hover;
    border: 1px solid $primary;
}
ModernCard[clickable="true"]:hover {
    background: $bg_card_hover;
    border: 1px solid $primary;
}
ModernCard[selected="true"] {
    background: #282a31;
    border: 2px solid $primary;
}

/* ==================== Роли текстов (QLabel[role=...]) ==================== */
QLabel[role="h1"] { font-size: 22px; font-weight: 700; }
QLabel[role="h2"] { font-size: 17px; font-weight: 600; }
QLabel[role="h3"] { font-size: 15px; font-weight: 600; }
QLabel[role="subtitle"] { font-size: 13px; color: $text_secondary; }
QLabel[role="caption"] { font-size: 12px; color: $text_secondary; }
QLabel[role="small"] { font-size: 11px; color: $text_secondary; }
QLabel[role="accent"] { color: $primary_light; font-weight: 600; }
QLabel[role="error"] { color: $danger_text; }
QLabel[role="logo"] { font-size: 22px; font-weight: 700; }
QLabel[role="logoSub"] { font-size: 12px; color: rgba(255, 255, 255, 0.65); }
QLabel[role="accentTitle"] { font-size: 20px; font-weight: 700; color: #ffffff; }
QLabel[role="percent"] { font-size: 20px; font-weight: 700; color: $primary_light; }
QLabel[role="statusIcon"] { font-size: 14px; color: $primary_light; }
QLabel[role="userName"] { font-size: 14px; font-weight: 600; }
QLabel[role="navCategory"] { font-size: 11px; font-weight: 700; color: $text_disabled; }

QLabel[role="methodName"] { font-size: 17px; font-weight: 600; }
QLabel[role="methodCategory"] {
    font-size: 11px;
    font-weight: 600;
    color: $text_secondary;
    border-top: 1px solid rgba(255, 255, 255, 0.25);
    padding-top: 6px;
}
QLabel[role="cardTitle"] { font-size: 16px; font-weight: 600; color: $primary_light; }
QLabel[role="cardText"] { font-size: 13px; color: $text_secondary; }

QLabel[role="iconBadge"] {
    font-size: 20px;
    background: rgba(120, 121, 241, 0.15);
    color: $primary_light;
    border: 1px solid rgba(120, 121, 241, 0.35);
    border-radius: 8px;
}
QLabel[role="methodBadge"] {
    color: $primary_light;
    font-size: 10px;
    font-weight: 700;
    background: rgba(120, 121, 241, 0.12);
    border: 1px solid rgba(120, 121, 241, 0.3);
    border-radius: 4px;
    padding: 2px 6px;
}
QLabel[role="errorBox"] {
    color: $danger_text;
    background: rgba(239, 68, 68, 0.10);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 7px;
    padding: 10px;
}
QLabel[role="noticeBox"] {
    color: $primary_light;
    background: rgba(120, 121, 241, 0.10);
    border: 1px solid $primary;
    border-radius: 7px;
    padding: 8px 14px;
}
QLabel[role="infoBox"] {
    color: $text_secondary;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid $border;
    border-radius: 8px;
    padding: 12px;
}
QLabel[role="infoKey"] { font-size: 11px; font-weight: 500; color: $text_secondary; }
QLabel[role="infoValue"] { font-size: 14px; font-weight: 600; }
QLabel[role="graphPlaceholder"] { font-size: 32px; color: rgba(255, 255, 255, 0.4); }
QLabel[role="imagePlaceholder"] { font-size: 24px; color: rgba(255, 255, 255, 0.5); }

/* ==================== Именованные панели (objectName) ==================== */
#pageHeader {
    background: $bg_panel;
    border-bottom: 1px solid $border;
}
#accentHeader {
    background: $primary;
}
#sidebar {
    background: $bg_sidebar;
    border-right: 1px solid $border;
}
#sidebarHeader {
    background: $primary;
}
#sidebarFooter {
    border-top: 1px solid $border;
}
#settingsSidebar {
    background: $bg_panel;
    border-right: 1px solid $border;
}
#progressPanel {
    background: #232428;
    border-bottom: 1px solid $border;
}
#graphPreview {
    background: $bg_app;
    border: 1px solid $border;
    border-radius: 8px;
}
#divider {
    background: $border;
}
#infoPanel {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid $border;
    border-radius: 8px;
}
#progressSeg {
    background: rgba(255, 255, 255, 0.10);
    border-radius: 4px;
}
#progressSeg[state="active"], #progressSeg[state="done"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $primary, stop:1 $primary_light);
}

HeaderWidget {
    background: $bg_panel;
    border-bottom: 1px solid $border;
}
""")

APP_QSS = _QSS.substitute(_TOKENS)


def repolish(widget):
    """Перечитать QSS после смены динамического свойства."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def _dark_palette():
    """Тёмная палитра — страховка от светлых дефолтных
    поверхностей (viewport'ы, диалоги, нативные панели)."""
    from PyQt6.QtGui import QPalette, QColor
    p = QPalette()
    window = QColor('#1a1b1e')
    base = QColor('#26272c')
    text = QColor('#ffffff')
    disabled = QColor(255, 255, 255, 90)
    p.setColor(QPalette.ColorRole.Window, window)
    p.setColor(QPalette.ColorRole.WindowText, text)
    p.setColor(QPalette.ColorRole.Base, base)
    p.setColor(QPalette.ColorRole.AlternateBase, QColor('#1e1f23'))
    p.setColor(QPalette.ColorRole.Text, text)
    p.setColor(QPalette.ColorRole.Button, QColor('#2e2f35'))
    p.setColor(QPalette.ColorRole.ButtonText, text)
    p.setColor(QPalette.ColorRole.Highlight, QColor('#7879F1'))
    p.setColor(QPalette.ColorRole.HighlightedText, text)
    p.setColor(QPalette.ColorRole.PlaceholderText, disabled)
    for group in (QPalette.ColorGroup.Disabled,):
        p.setColor(group, QPalette.ColorRole.WindowText, disabled)
        p.setColor(group, QPalette.ColorRole.Text, disabled)
        p.setColor(group, QPalette.ColorRole.ButtonText, disabled)
    return p


def apply_theme(app):
    """Применить тему один раз на уровне QApplication."""
    from PyQt6.QtGui import QFont
    app.setFont(QFont("Segoe UI", 10))
    app.setPalette(_dark_palette())
    app.setStyleSheet(APP_QSS)

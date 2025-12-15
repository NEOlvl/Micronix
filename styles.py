"""
Common styles and style utilities
"""


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
import math
import scipy.optimize


def solve_for_x_1(h2, t, L=40.0):
    """
    Решает уравнение: cot(x/2)/(x/2) - 2*tan(h2*L)/(h2*t) = 0

    Parameters:
    h2: float - известный параметр
    t: float - толщина (0.5-2.5 мм)
    L: float = 40.0 мм

    Returns:
    float - решение x (в радианах)
    """
    # Вычисляем правую часть (константу A)
    A = 2 * math.tan(h2 * L) / (h2 * t)

    # Определяем функцию для решения
    def equation(x):
        if abs(x) < 1e-10:  # избегаем деления на 0
            return math.inf
        u = x / 2
        return math.cos(u) / (math.sin(u) * u) - A

    # Ищем решение численно
    # Начальное приближение - обычно решение находится в (0, π)
    try:
        # Пробуем несколько начальных приближений
        for x0 in [1.0, 2.0, 3.0]:
            result = scipy.optimize.root_scalar(equation, x0=x0, method='newton')
            if result.converged and 0 < result.root < 4 * math.pi:
                return result.root

        # Если не сработало, используем метод Брента на интервале
        result = scipy.optimize.root_scalar(equation, bracket=[0.1, 3.0], method='brentq')
        if result.converged:
            return result.root

    except (ValueError, RuntimeError):
        # Резервный метод если первые не сработали
        try:
            result = scipy.optimize.minimize_scalar(lambda x: abs(equation(x)), bounds=[0.1, 6.0], method='bounded')
            return result.x
        except:
            return math.pi  # возвращаем значение по умолчанию

    return math.pi  # значение по умолчанию если все методы не сработали


def solve_for_x_2(beta2, t, L=40.0):
    """
    Решает уравнение: cot(x/2)/(x/2) - 2*tanh(beta2*L)/(beta2*t) = 0

    Parameters:
    beta2: float - известный параметр
    t: float - толщина (0.5-2.5 мм)
    L: float = 40.0 мм

    Returns:
    float - решение x (в радианах)
    """
    # Вычисляем правую часть (константу A)
    A = 2 * math.tanh(beta2 * L) / (beta2 * t)

    # Определяем функцию для решения
    def equation(x):
        if abs(x) < 1e-10:  # избегаем деления на 0
            return math.inf
        u = x / 2
        # cot(u)/u = cos(u)/(sin(u)*u)
        return math.cos(u) / (math.sin(u) * u) - A

    # Ищем решение численно
    try:
        # Пробуем несколько начальных приближений
        for x0 in [1.0, 2.0, 3.0, 4.0]:
            result = scipy.optimize.root_scalar(equation, x0=x0, method='newton')
            if result.converged and 0 < result.root < 4 * math.pi:
                return result.root

        # Если не сработало, используем метод Брента на интервале
        result = scipy.optimize.root_scalar(equation, bracket=[0.1, 3.0], method='brentq')
        if result.converged:
            return result.root

    except (ValueError, RuntimeError):
        # Резервный метод если первые не сработали
        try:
            result = scipy.optimize.minimize_scalar(lambda x: abs(equation(x)), bounds=[0.1, 6.0], method='bounded')
            return result.x
        except:
            return math.pi  # возвращаем значение по умолчанию

    return math.pi  # значение по умолчанию если все методы не сработали
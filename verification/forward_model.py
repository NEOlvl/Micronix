"""Независимая прямая модель резонатора с образцом (ТЗ2-3).

Дисперсионные уравнения записаны заново и решаются в прямую сторону:
по заданной диэлектрической проницаемости eps и геометрии ищется
резонансная частота fE (для МФЧ — смещение поршня delL на
фиксированной частоте). Код методов backend.core.calculator здесь
не используется — независимость прямой задачи от обратной и есть
суть верификации.

Размеры в мм, частоты в Гц, c в мм/с.
"""

import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import jv, yn

C = 299.792458e9      # скорость света, мм/с
EB = 1.0006           # диэлектрическая проницаемость воздуха
V11 = 3.831706        # первый корень J1 (мода H01)


class ForwardModelError(Exception):
    """Прямая задача не имеет решения на заданном интервале."""


def _k2(f_hz: float) -> float:
    """Волновое число в воздушной среде, 1/мм."""
    return 2.0 * math.pi * f_hz * math.sqrt(EB) / C


def _k0(f_hz: float) -> float:
    """Волновое число в вакууме, 1/мм.

    ТЗ3-5: волновое число внутри образца считается от вакуума —
    eps здесь относительно вакуума (eps_в = 1.0006 для воздуха),
    как и в методах backend.core.calculator (E = (C/2πfE)^2*...).
    """
    return 2.0 * math.pi * f_hz / C


def _scan_root(func, lo: float, hi: float, n: int = 8000) -> float:
    """Наибольший корень func на [lo, hi] сканированием по сетке.

    Сетка просматривается от hi к lo; пересмена знака даёт скобку для
    brentq. Подделка знакосмены полюсом отбраковывается проверкой
    остатка |func(root)|.
    """
    xs = np.linspace(lo, hi, n)
    prev_x = prev_y = None
    for i in range(n - 1, -1, -1):
        x = xs[i]
        try:
            y = func(x)
        except (ValueError, ZeroDivisionError, OverflowError):
            prev_x = prev_y = None
            continue
        if not math.isfinite(y):
            prev_x = prev_y = None
            continue
        if prev_y is not None and y * prev_y < 0:
            r = brentq(func, x, prev_x, xtol=1.0, rtol=1e-12)
            try:
                resid = func(r)
            except (ValueError, ZeroDivisionError, OverflowError):
                resid = float('nan')
            if math.isfinite(resid) and abs(resid) < 1e-9:
                return r
            # пересмена знака — полюс, а не корень; идём дальше вниз
        prev_x, prev_y = x, y
    raise ForwardModelError(
        f"Корень прямой задачи не найден на [{lo:.6g}; {hi:.6g}]")


def fe_mfd(eps: float, t: float, a: float, L0: float,
           f0: float) -> float:
    """Прямая задача МФД: fE образца у торцевой стенки резонатора.

    tg(x)/x + tg[h2*(L0-t)]/(h2*t) = 0,  x = t*sqrt(eps*k0^2 - (v11/a)^2).
    """
    def f(fe):
        k2 = _k2(fe)
        q2 = k2 * k2 - (V11 / a) ** 2
        xd2 = eps * _k0(fe) ** 2 - (V11 / a) ** 2
        if xd2 <= 0.0:
            return float('nan')
        x = t * math.sqrt(xd2)
        if q2 > 0.0:
            h2 = math.sqrt(q2)
            return math.tan(x) / x + math.tan(h2 * (L0 - t)) / (h2 * t)
        # закритический режим: воздушная часть — затухающая волна
        b2 = math.sqrt(-q2)
        return math.tan(x) / x + math.tanh(b2 * (L0 - t)) / (b2 * t)

    return _scan_root(f, 0.3 * f0, f0)


def delL_mfch(eps: float, t: float, a: float, f0: float) -> float:
    """Прямая задача МФЧ: смещение поршня delL на фиксированной f0.

    tg[h2*(delL+t)]/(h2*t) = tg(x)/x -> delL = atan(h2*t*tg(x)/x)/h2 - t
    (наименьшее неотрицательное delL по ветвям arctg + n*pi/h2).
    """
    k2 = _k2(f0)
    h2 = math.sqrt(k2 * k2 - (V11 / a) ** 2)
    x = t * math.sqrt(eps * _k0(f0) ** 2 - (V11 / a) ** 2)
    v = h2 * t * math.tan(x) / x
    delL = math.atan(v) / h2 - t
    while delL < 0.0:
        delL += math.pi / h2
    return delL


def fe_so(eps: float, a: float, R0: float, L: float, p: float,
          f0: float) -> float:
    """Прямая задача СО: fE стержня на оси цилиндрического резонатора.

    J1(x)/(x*J0(x)) = Z1(y)/(y*Z0(y)),
    x = a*sqrt(eps*k0^2 - h^2),  y = a*sqrt(k2^2 - h^2),  h = p*pi/L,
    Zi(u) = Ji(u) - [J1(y*b)/N1(y*b)] * Ni(u),  b = R0/a.
    """
    b = R0 / a
    h = p * math.pi / L

    def f(fe):
        k2 = _k2(fe)
        y2 = (k2 * a) ** 2 - (h * a) ** 2
        x2 = eps * (_k0(fe) * a) ** 2 - (h * a) ** 2
        if y2 <= 0.0 or x2 <= 0.0:
            return float('nan')
        y, x = math.sqrt(y2), math.sqrt(x2)
        j1b, n1b = jv(1, y * b), yn(1, y * b)
        if abs(n1b) < 1e-30:
            return float('nan')
        k = j1b / n1b
        z1 = jv(1, y) - k * yn(1, y)
        z0 = jv(0, y) - k * yn(0, y)
        if abs(x * jv(0, x)) < 1e-30 or abs(y * z0) < 1e-30:
            return float('nan')
        return jv(1, x) / (x * jv(0, x)) - z1 / (y * z0)

    return _scan_root(f, 0.3 * f0, f0)


def fe_msr9(eps: float, t: float, a: float, L0: float,
            f0: float) -> float:
    """Прямая задача MSR9: fE образца в середине резонатора.

    (x/t)*tg(x/2) = h2*ctg(h2*L0/2),
    x = t*sqrt(eps*k0^2 - (v11/a)^2),  h2 = sqrt(k2^2 - (v11/a)^2).
    ТЗ3-6: L0 — длина пустого резонатора (ГОСТ §11: L0 = 2L);
    воздушные секции по L0/2, полость с образцом — L0 + t.
    """
    def f(fe):
        k2 = _k2(fe)
        q2 = k2 * k2 - (V11 / a) ** 2
        xd2 = eps * _k0(fe) ** 2 - (V11 / a) ** 2
        if xd2 <= 0.0:
            return float('nan')
        x = t * math.sqrt(xd2)
        lhs = (x / t) * math.tan(x / 2.0)
        if q2 > 0.0:
            h2 = math.sqrt(q2)
            return lhs - h2 / math.tan(h2 * L0 / 2.0)
        # закритический режим: воздушная часть — затухающая волна
        b2 = math.sqrt(-q2)
        return lhs - b2 / math.tanh(b2 * L0 / 2.0)

    return _scan_root(f, 0.3 * f0, f0)

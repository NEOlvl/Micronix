"""Обработка АЧХ: выделение параметров резонанса f0, f1, f2, Q.

Алгоритм (ТЗ-5):
1. Лёгкое сглаживание (Савицкий–Голей) — подавление шума без размытия
   резонансного провала.
2. Оценка базовой линии: при наличии соседних мод — локальная прямая
   через межмодовые седловины (реальные АЧХ многомодовы), иначе —
   робастная линейная аппроксимация по краевым зонам диапазона
   с отбрасыванием точек, попавших в провалы.
3. Переход в линейную шкалу мощности p = 10^(A/10).
4. Уровень половинной мощности: w(f) = p_base(f) - p(f), порог w_max / 2
   (для глубокого провала эквивалентно -3 дБ относительно базы).
5. Частоты пересечений f1, f2 — линейная интерполяция между отсчётами.
6. Уточнение f0 параболической интерполяцией минимума.

Вырожденные случаи (нет резонанса, резонанс у края, недостаточная
глубина, f1 >= f2) — контролируемая ошибка ResonanceError.
"""

from dataclasses import dataclass, field
from typing import List, Sequence

import numpy as np
from scipy.signal import savgol_filter


class ResonanceError(Exception):
    """Контролируемая ошибка выделения резонанса из АЧХ."""


@dataclass
class ResonanceParameters:
    """Параметры резонанса, выделенные из АЧХ."""

    f0: float          # резонансная частота, Гц
    f1: float          # левая граница полосы половинной мощности, Гц
    f2: float          # правая граница полосы половинной мощности, Гц
    a0: float          # амплитуда в точке резонанса, дБ
    baseline: float    # уровень базовой линии в точке f0, дБ
    depth_db: float    # глубина провала относительно базы, дБ
    q: float           # добротность f0 / (f2 - f1)
    index: int         # индекс отсчёта экстремума в отсортированном массиве
    warnings: List[str] = field(default_factory=list)


_MIN_DEPTH_DB = 1.0   # провал мельче — резонанс не считается обнаруженным


def _savgol_window(n: int) -> int:
    """Минимальное нечётное окно сглаживания (5 точек).

    Окно используется только для устойчивой локализации экстремума;
    расчёты ведутся по сырым данным — узкие провалы (единицы отсчётов)
    широким окном сильно искажаются по глубине и ширине.
    """
    return min(5, n if n % 2 == 1 else n - 1)


def _parabolic_vertex(y: np.ndarray, i: int) -> float:
    """Смещение вершины параболы от точки i, в долях шага (-0.5..0.5)."""
    if i <= 0 or i >= len(y) - 1:
        return 0.0
    denom = y[i - 1] - 2.0 * y[i] + y[i + 1]
    if denom == 0.0:
        return 0.0
    shift = 0.5 * (y[i - 1] - y[i + 1]) / denom
    return float(np.clip(shift, -0.5, 0.5))


def _robust_baseline(f: np.ndarray, a: np.ndarray,
                     edge_idx: np.ndarray, dip_sign: float,
                     iterations: int = 3) -> np.ndarray:
    """Линейная базовая линия по краевым зонам.

    Итеративно отбрасывает точки, уходящие в сторону резонанса
    (для 'dip' — провалы ниже линии, для 'peak' — пики выше),
    чтобы хвосты соседних мод не перекашивали оценку.
    """
    coef = np.polyfit(f[edge_idx], a[edge_idx], 1)
    idx = edge_idx
    for _ in range(iterations):
        resid = a[idx] - np.polyval(coef, f[idx])
        med = np.median(resid)
        mad = 1.4826 * np.median(np.abs(resid - med))
        # порог отбрасывания в сторону резонанса, не меньше 0.5 дБ
        thr = max(0.5, med + 3.0 * mad)
        keep = dip_sign * resid > -thr if dip_sign > 0 else resid < thr
        if keep.all() or keep.sum() < 4:
            break
        idx = idx[keep]
        coef = np.polyfit(f[idx], a[idx], 1)
    return np.polyval(coef, f)


def _dip_boundaries(a_s: np.ndarray, i0: int, dip_sign: float,
                    min_prominence_db: float = 2.0) -> tuple:
    """Границы резонанса: ближайшие межмодовые седловины.

    От экстремума i0 идём наружу в обе стороны до первого поворота,
    после которого кривая опускается в соседнюю моду не менее чем на
    min_prominence_db — только такая точка является настоящей седловиной.
    Шумовые микроповороты на плече провала или на плоской базовой линии
    не считаются границами. Используется для локальной базовой линии:
    реальные АЧХ многомодовы, кривая между провалами не возвращается
    к номинальной базе краёв диапазона.
    """
    n = len(a_s)
    a0 = a_s[i0]
    bounds = []
    for step in (-1, 1):
        i, found = i0, None
        while True:
            nxt = i + step
            if not (0 <= nxt < n):
                break
            if dip_sign * (a_s[nxt] - a_s[i]) <= 0:
                # i — точка поворота; замеряем глубину спуска после неё:
                # седловина считается, только если за поворотом следует
                # спуск в соседнюю моду >= min_prominence_db
                if (dip_sign * (a_s[i] - a0) > min_prominence_db
                        and abs(i - i0) >= 2):
                    j = i
                    while (0 <= j + step < n
                           and dip_sign * (a_s[j + step] - a_s[j]) <= 0):
                        j += step
                    descent = dip_sign * (a_s[i] - a_s[j])
                    if descent >= min_prominence_db:
                        found = i
                        break
                # шумовой поворот или плато — идём дальше
            i = nxt
        bounds.append(found)
    return bounds[0], bounds[1]


def _find_half_power_crossing(freq: np.ndarray, w: np.ndarray,
                              level: float, i0: int, side: str,
                              stop: int = None) -> float:
    """Частота пересечения w(f) = level слева/справа от i0 (интерполяция).

    Движемся от экстремума наружу до первой точки ниже уровня;
    пересечение — между ней и предыдущей (выше уровня). stop — индекс
    седловой границы провала, за которую нельзя выходить.
    """
    side_name = 'слева' if side == 'left' else 'справа'
    if side == 'left':
        limit = 0 if stop is None else stop
        i = i0 - 1
        while i >= limit and w[i] >= level:
            i -= 1
        if i < limit:
            raise ResonanceError(
                f"Граница полосы половинной мощности не найдена {side_name} "
                "от резонанса — провал не возвращается к базовой линии")
        i_lo, i_hi = i, i + 1
    else:
        limit = len(w) - 1 if stop is None else stop
        i = i0 + 1
        while i <= limit and w[i] >= level:
            i += 1
        if i > limit:
            raise ResonanceError(
                f"Граница полосы половинной мощности не найдена {side_name} "
                "от резонанса — провал не возвращается к базовой линии")
        i_lo, i_hi = i - 1, i

    w_lo, w_hi = w[i_lo], w[i_hi]
    frac = (level - w_lo) / (w_hi - w_lo)
    return float(freq[i_lo] + frac * (freq[i_hi] - freq[i_lo]))


def extract_resonance(frequencies: Sequence[float],
                      amplitudes: Sequence[float],
                      peak: str = 'dip',
                      edge_fraction: float = 0.08,
                      smooth: bool = True) -> ResonanceParameters:
    """Выделить параметры резонанса из АЧХ.

    Args:
        frequencies: частоты, Гц (монотонные).
        amplitudes: амплитуды, дБ.
        peak: 'dip' — резонанс как провал (передача через резонатор);
              'peak' — резонанс как максимум.
        edge_fraction: доля точек по краям для оценки базовой линии.
        smooth: сглаживать кривую перед поиском.

    Returns:
        ResonanceParameters (f0, f1, f2, A0, baseline, Q и т.д.).

    Raises:
        ResonanceError: резонанс не обнаружен или полоса не определяется.
    """
    f = np.asarray(frequencies, dtype=float)
    a = np.asarray(amplitudes, dtype=float)
    n = f.size

    if n != a.size:
        raise ResonanceError("Длины массивов частот и амплитуд не совпадают")
    if n < 16:
        raise ResonanceError(f"Слишком мало точек АЧХ: {n} (нужно >= 16)")
    if not (np.isfinite(f).all() and np.isfinite(a).all()):
        raise ResonanceError("АЧХ содержит NaN или бесконечные значения")

    order = np.argsort(f)
    if not np.array_equal(order, np.arange(n)):
        f, a = f[order], a[order]
    if np.any(np.diff(f) <= 0):
        raise ResonanceError("Массив частот содержит повторяющиеся значения")

    warnings: List[str] = []

    # Лёгкое сглаживание только для устойчивой локализации экстремума;
    # измерения ведутся по сырым данным, чтобы не искажать узкий провал.
    a_s = savgol_filter(a, _savgol_window(n), 2) if smooth else a.copy()

    # Экстремум (самый глубокий провал/пик); защита от краёв диапазона
    i0 = int(np.argmin(a_s) if peak == 'dip' else np.argmax(a_s))
    edge_n = max(4, int(edge_fraction * n))
    if i0 < edge_n or i0 > n - 1 - edge_n:
        raise ResonanceError(
            f"Экстремум АЧХ в точке {f[i0]:.6g} Гц находится у края диапазона — "
            "невозможно достоверно определить резонанс и базовую линию")

    # Базовая линия: локальная — прямая через седловые границы провала;
    # если граница не найдена — глобальная робастная оценка по краям
    dip_sign = 1.0 if peak == 'dip' else -1.0
    bl, br = _dip_boundaries(a_s, i0, dip_sign)
    local_baseline = bl is not None and br is not None
    if local_baseline:
        coef = np.polyfit([f[bl], f[br]], [a_s[bl], a_s[br]], 1)
        baseline_f = np.polyval(coef, f)
    else:
        # седловин нет с обеих сторон — одиночная мода, глобальная база;
        # седловина с одной стороны — асимметрия, предупреждаем
        if (bl is None) != (br is None):
            side = 'слева' if bl is None else 'справа'
            warnings.append(
                f"Локальная базовая линия недоступна {side} от резонанса "
                "— использована глобальная")
        edge_idx = np.r_[0:edge_n, n - edge_n:n]
        baseline_f = _robust_baseline(f, a, edge_idx, dip_sign)

    # Линейная шкала мощности и глубина провала w(f) — по сырым данным:
    # сглаживание заметно искажает глубину и ширину узких провалов.
    # Клиппинг базовой линии защищает от экстраполяционного разлёта
    # прямой через седловины.
    p = 10.0 ** (a / 10.0)
    p_base = 10.0 ** (np.clip(baseline_f, -350.0, 350.0) / 10.0)
    w = (p_base - p) if peak == 'dip' else (p - p_base)

    w_max = float(w[i0])
    a0 = float(a[i0])
    baseline_0 = float(baseline_f[i0])
    p_raw = 10.0 ** (a0 / 10.0)
    depth_db = abs(float(10.0 * np.log10(max(p_base[i0], 1e-30) / max(p_raw, 1e-30))))

    if w_max <= 0.0 or depth_db < _MIN_DEPTH_DB:
        raise ResonanceError(
            f"Резонансный провал относительно базовой линии не обнаружен "
            f"(глубина {depth_db:.2f} дБ < {_MIN_DEPTH_DB} дБ)")
    if depth_db < 3.01:
        warnings.append(
            f"Глубина резонанса {depth_db:.2f} дБ меньше 3 дБ — "
            "полоса половинной мощности выходит за глубину провала")
    elif depth_db < 6.0:
        warnings.append(
            f"Малая глубина резонанса {depth_db:.2f} дБ — оценка Q шумозависима")

    # Полоса половинной мощности — линейная интерполяция пересечений
    # по сырым данным; при локальной базе поиск ограничен границами провала
    half = w_max / 2.0
    f1 = _find_half_power_crossing(f, w, half, i0, 'left', stop=bl)
    f2 = _find_half_power_crossing(f, w, half, i0, 'right', stop=br)
    df = float(np.median(np.diff(f)))
    f0 = float(f[i0] + _parabolic_vertex(a_s, i0) * df)

    if f2 <= f1:
        raise ResonanceError(f"Вырождение полосы: f1={f1:.6g}, f2={f2:.6g}")
    if f2 - f1 < 8.0 * df:
        warnings.append(
            f"Низкая дискретизация резонанса: полоса {f2 - f1:.4g} Гц "
            f"занимает менее 8 отсчётов — оценка Q грубая")

    return ResonanceParameters(
        f0=f0, f1=f1, f2=f2, a0=a0,
        baseline=baseline_0, depth_db=depth_db,
        q=f0 / (f2 - f1), index=i0, warnings=warnings)


def extract_resonance_db(frequencies: Sequence[float],
                         amplitudes: Sequence[float],
                         **kwargs) -> dict:
    """Совместимая обёртка: результат словарём (как старый find_resonance_parameters)."""
    r = extract_resonance(frequencies, amplitudes, **kwargs)
    return {
        'f0': r.f0, 'f1': r.f1, 'f2': r.f2,
        'A0': r.a0, 'Q': r.q, 'idx_min': r.index,
        'baseline': r.baseline, 'depth_db': r.depth_db,
        'warnings': r.warnings,
    }

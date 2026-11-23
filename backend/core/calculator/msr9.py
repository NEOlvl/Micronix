"""Универсальный резонаторный метод (волна H01p, нечётный p = 1 или 3).

Оформление MSR_9.py модулем (ТЗ-6): убраны input()/print()/sys.exit()
и глобальные переменные; расчёт — по параметрам и резонансным каналам.

Отличие от МФЧ: поддерживает случай fE ниже частоты отсечки fc
(затухающая волна, решатель solve_for_x_2).

Условие применимости: t <= c / (5 * fE * sqrt(E)).
"""

import math
from typing import Dict

from .base import (CalculationError, Method, MethodInput, MethodResult,
                   ResonanceChannels)
from .const import (C, EB, F_RANGE, MSR9_E_RANGE, MSR9_TGO_RANGE,
                    V11)
from .res_x import solve_for_x_1, solve_for_x_2

# частота отсечки резонатора: fc = C * V11 / (2*pi*a*sqrt(EB))


class UniversalResonatorMethod(Method):
    id = 'msr9'
    name = 'Универсальный резонатор (H01p)'
    standard = 'ГОСТ Р 8.623-2015'
    description = (
        'Резонатор H01p с нечётным индексом p: образец в середине '
        'резонатора, поддерживается режим fE ниже частоты отсечки.')
    inputs = (
        MethodInput('t', 'Толщина образца', 'мм', (0.5, 6.0)),
        MethodInput('D', 'Диаметр резонатора', 'мм', (5.0, 200.0)),
        MethodInput('L0', 'Длина резонатора', 'мм', (10.0, 500.0)),
        MethodInput('p', 'Индекс волны p (1 или 3)', '', (1.0, 3.0),
                    default=1.0),
    )
    resonance_fields = ('f0', 'f1', 'f2', 'a0', 'fe', 'f1e', 'f2e', 'ae')

    def calculate(self, params: Dict,
                  resonance: ResonanceChannels) -> MethodResult:
        res = MethodResult()
        res.errors.extend(self.validate(params))
        res.errors.extend(resonance.require(*self.resonance_fields))
        if res.errors:
            return res

        v = self.get_values(params)
        t, D, L0, p = v['t'], v['D'], v['L0'], v['p']
        if int(p) not in (1, 3):
            res.errors.append(f"Неподходящий индекс волны p = {p:g} (1 или 3)")
            return res
        f0, f1, f2, A0 = resonance.f0, resonance.f1, resonance.f2, resonance.a0
        fE, f1E, f2E, AE = resonance.fe, resonance.f1e, resonance.f2e, resonance.ae
        for name, f in (('f0', f0), ('fE', fE)):
            if not (F_RANGE[0] <= f <= F_RANGE[1]):
                res.errors.append(f"Неправильное значение {name} = {f:.6g} Гц")
                return res

        try:
            a = 0.5 * D
            L = L0 / 2.0
            fc = C * V11 / (2.0 * math.pi * a * math.sqrt(EB))
            k2 = 2.0 * math.pi * fE * math.sqrt(EB) / C

            if fE >= fc:
                h2 = math.sqrt(k2 ** 2 - (V11 / a) ** 2)
                x = solve_for_x_1(h2, t, L)
                O = math.atan(math.tan(h2 * L) * x / (h2 * t))
                Rii = math.sin(O) ** 2 / math.sin(h2 * L) ** 2
                F2 = 1.0 - math.sin(2.0 * h2 * L) / (2.0 * h2 * L)
                n_extra = (2.0 * ((h2 * a) / V11) ** 2 + L0 * F2 / a)
            else:
                beta2 = math.sqrt((V11 / a) ** 2 - k2 ** 2)
                x = solve_for_x_2(beta2, t, L)
                O = math.atan(math.tanh(beta2 * L) * x / (beta2 * t))
                Rii = math.sin(O) ** 2 / math.sinh(beta2 * L) ** 2
                F2 = 1.0 - math.sinh(2.0 * beta2 * L) / (2.0 * beta2 * L)
                n_extra = (L0 * F2 / a - 2.0 * ((beta2 * a) / V11) ** 2)

            E = (C / (2.0 * math.pi * fE)) ** 2 * \
                ((x / t) ** 2 + (V11 / a) ** 2)
            F1 = 1.0 - (math.sin(2.0 * (x + O)) - math.sin(2.0 * O)) \
                / (2.0 * x)
            K1E = 1.0 / (1.0 + Rii * (L0 * F2) / (E * t * F1))
            G = a * (L0 + t) / ((2.0 * a - (L0 + t))
                              * (p * C / (2.0 * (L0 + t) * f0
                                          * math.sqrt(EB))) ** 2
                              + (L0 + t))
            Q0 = f0 / (f2 - f1)
            QE = fE / (f2E - f1E)  # Д-2: полоса нагруженного резонанса
            Q00 = Q0 / (1.0 - 10.0 ** (0.05 * A0))
            Q0E = QE / (1.0 - 10.0 ** (0.05 * AE))
            n = (G * math.sqrt(f0 / fE) * (V11 / (k2 * a)) ** 2
                 * (F1 * t / a + Rii * n_extra)
                 / (E * t * F1 + Rii * L0 * F2))
            tg0 = (1.0 / K1E) * (1.0 / Q0E - n / Q00)
        except (CalculationError, ValueError, ZeroDivisionError,
                OverflowError) as exc:
            res.errors.append(f"Ошибка расчёта: {exc}")
            return res

        if not (MSR9_E_RANGE[0] <= E <= MSR9_E_RANGE[1]):
            res.errors.append(
                f"Неподходящая диэлектрическая проницаемость E = {E:.6g}")
        if not (MSR9_TGO_RANGE[0] <= tg0 <= MSR9_TGO_RANGE[1]):
            res.errors.append(
                f"Неподходящий тангенс угла диэлектрических потерь "
                f"tgo = {tg0:.6g}")
        if E > 0 and t > C / (5.0 * fE * math.sqrt(E)):
            res.warnings.append(
                "Нарушено условие применимости метода: "
                "t > c/(5*fE*sqrt(E)) — результат ориентировочный")

        res.values = {'E': E, 'tgo': tg0, 'Q0': Q0, 'QE': QE,
                      'x': x, 'K1E': K1E, 'fc': fc}
        return res


METHOD = UniversalResonatorMethod()

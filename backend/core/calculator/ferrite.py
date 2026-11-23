"""СВЧ-ферриты (СВЧФ) — унаследованная расчётная модель.

ВНИМАНИЕ: сверка с ГОСТ Р 71432-2024 показала, что реализованные
здесь формулы (через волновые числа (c/2πfE)²-(h/2π)² и коэффициент
заполнения k) НЕ соответствуют эмпирическим формулам ГОСТ 71432
(пп. 4.6.1-4.6.5, 5.6.1-5.6.3 — через относительный сдвиг частоты δf,
изменение затухания Ad и поперечную магнитную проницаемость μ⊥).
Модуль сохранён как рабочая наследственная модель для совместимости
с архивными измерениями; приведение к ГОСТ 71432 — отдельная задача.

Перенос Methot_Egor, Methot_Egor_st и Method_real из All_Methods_3.py
с исправлениями:
- Д-1, Д-5: результат — структурированный MethodResult (устаревший код
  возвращал строку "Значение tgdelE = ..." либо всегда "ok")
- Д-2: добротность с образцом — по собственной полосе нагруженного
  резонанса

Варианты расчёта (поле params['variant']):
  st     — стандартный расчёт (бывш. Methot_Egor_st)
  real   — полный расчёт (бывш. Method_real)
  circle — по сдвигу резонансной частоты, круглый образец
  square — по сдвигу резонансной частоты, квадратный образец
"""

import math
from typing import Dict

from .base import (CalculationError, Method, MethodInput, MethodResult,
                   ResonanceChannels)

_E_FERRITE_MAX = 500.0


class FerriteMethod(Method):
    id = 'svchf'
    name = 'СВЧ-ферриты (СВЧФ)'
    standard = 'унаследованная модель (не ГОСТ Р 71432-2024)'
    category = 'Ферриты'
    description = (
        'Диэлектрические свойства ферритов по сдвигу и уширению '
        'резонансной кривой: стандартный, полный расчёт и метод '
        'сдвига частоты (круглый/квадратный образец). '
        'ВНИМАНИЕ: методика не соответствует ГОСТ Р 71432-2024 '
        '(унаследованная модель).')
    variants = {
        'st': 'Стандартный расчёт',
        'real': 'Полный расчёт',
        'circle': 'Сдвиг частоты (круглый образец)',
        'square': 'Сдвиг частоты (квадратный образец)',
    }
    inputs = (
        MethodInput('R', 'Радиус резонатора', 'мм', (0.5, 100.0)),
        MethodInput('r', 'Радиус образца', 'мм', (0.01, 50.0)),
        MethodInput('a', 'Сторона a образца', 'мм', (0.01, 50.0),
                    variants=('square',)),
        MethodInput('b', 'Сторона b образца', 'мм', (0.01, 50.0),
                    variants=('square',)),
        MethodInput('deld', 'Изменение полосы пропускания', '', (0.0, 1.0),
                    variants=('circle', 'square')),
        MethodInput('Ms', 'Намагниченность насыщения', '', (0.0, 1e6),
                    variants=('circle', 'square')),
    )

    def _variant(self, params: Dict) -> str:
        return str(params.get('variant') or 'st')

    def calculate(self, params: Dict,
                  resonance: ResonanceChannels) -> MethodResult:
        res = MethodResult()
        # ТЗ2-7: методика не соответствует ГОСТ Р 71432-2024 —
        # предупреждение выводится в GUI и PDF-протоколе
        res.warnings.append(
            'Методика СВЧФ не соответствует ГОСТ Р 71432-2024 '
            '(унаследованная модель)')
        variant = self._variant(params)
        if variant not in self.variants:
            res.errors.append(
                f"Неизвестный вариант расчёта '{variant}' "
                f"(допустимы: {', '.join(self.variants)})")
            return res
        res.errors.extend(self.validate(params, variant))
        needed = ('f0', 'f1', 'f2', 'fe', 'f1e', 'f2e') \
            if variant in ('st', 'real') else ('f0', 'fe')
        res.errors.extend(resonance.require(*needed))
        if res.errors:
            return res

        v = self.get_values(params, variant)
        try:
            if variant == 'st':
                res.values = self._calc_st(v, resonance)
            elif variant == 'real':
                res.values = self._calc_real(v, resonance)
            else:
                res.values = self._calc_egor(v, resonance,
                                             square=(variant == 'square'))
        except (CalculationError, ValueError, ZeroDivisionError,
                OverflowError) as exc:
            res.errors.append(f"Ошибка расчёта: {exc}")
            return res

        E = res.values['E']
        if not (1.0 < E <= _E_FERRITE_MAX):
            res.errors.append(f"Неподходящее значение E = {E:.6g}")
        if not res.values['tgo'] > 0.0:
            res.errors.append(
                f"Неподходящее значение tgo = {res.values['tgo']:.6g}")
        return res

    @staticmethod
    def _calc_st(v: Dict, r: ResonanceChannels) -> Dict:
        """Стандартный расчёт (бывш. Methot_Egor_st)."""
        R, r_s = v['R'], v['r']
        E = 1.0 + 0.539 * (R / r_s) ** 2 * ((r.f0 - r.fe) / r.f0)
        Q0 = r.f0 / (r.f2 - r.f1)
        QE = r.fe / (r.f2e - r.f1e)
        tgo = (0.269 / E) * (R / r_s) ** 2 * (1.0 / QE - 1.0 / Q0)
        return {'E': float(E), 'tgo': float(tgo), 'Q0': Q0, 'QE': QE}

    @staticmethod
    def _calc_real(v: Dict, r: ResonanceChannels) -> Dict:
        """Полный расчёт (бывш. Method_real)."""
        R, r_s = v['R'], v['r']
        f0, fe, f10, f20 = r.f0, r.fe, r.f1, r.f2
        f1e, f2e = r.f1e, r.f2e
        delF0 = (f0 - fe) / f0
        mu = 1.05
        e_real = 1.085 * (1.0 + (
            (0.539 * (R ** 2 / r_s ** 2) * delF0) / 1.0 - delF0
            + (1.7 - 2.5 * delF0) * delF0) / (
            1.0 + (1.7 - 2.5 * delF0) * delF0
            + 0.39 * mu * delF0 * (1.0 - delF0)))
        K = 1.5
        d0 = 2.0 * abs(f10 - f20) / (f10 + f20)
        dx = 2.0 * abs(f1e - f2e) / (f1e + f2e)
        delD = dx - d0 / (1.0 + K)
        e_image = (
            (0.2726 * (R ** 2 / r_s ** 2) * delD) / (
                (1.0 - delF0) ** 2
                * (1.0 + delF0 * (0.486 + 1.56 * math.log(R / (2.14 * r_s)))) ** 2)
            * (1.0 + e_real * mu * 1.55 * (r_s ** 2 / R ** 2)
               * (1.0 - 1.53 * delF0))
        ) + (
            (e_real * 1.56 * (r_s ** 2 / R ** 2) * (1.0 - 1.53 * delF0)
             * (mu - 1.0) + e_real - 1.0)
            / (1.0 + e_real * mu * 1.55 * (r_s ** 2 / R ** 2)
               * (1.0 - 1.53 * delF0))
        ) * delD
        tgo = e_image / e_real
        return {'E': float(e_real), 'eps2': float(e_image),
                'tgo': float(tgo)}

    @staticmethod
    def _calc_egor(v: Dict, r: ResonanceChannels, square: bool) -> Dict:
        """Метод сдвига частоты (бывш. Methot_Egor, Д-5)."""
        R, r_s, deld, Ms = v['R'], v['r'], v['deld'], v['Ms']
        delf0 = (r.f0 - r.fe) / r.f0
        ushT = 0.000216666 * Ms + 1.03
        if not square:
            Esh = (1.085 * (1.0 + ((0.539 * R ** 2 * delf0) / r_s ** 2
                    / (1.0 - delf0)) + (1.7 - 2.5 * delf0) * delf0)
                   / (1.0 + (1.7 - 2.5 * delf0) * delf0
                      + 0.39 * ushT * delf0 * (1.0 - delf0)))
            Esh2 = (
                (0.2726 * (R ** 2 / r_s ** 2) * deld) / (
                    (1.0 - delf0) ** 2
                    * (1.0 + delf0 * (0.486 + 1.56 * math.log(R / (2.14 * r_s)))) ** 2
                    * (1.0 + Esh * ushT * 1.55 * (r_s ** 2 / R ** 2)
                       * (1.0 - 1.53 * delf0)))
            ) + (
                deld * (Esh * 1.56 * (r_s ** 2 / R ** 2) * (1.0 - 1.53 * delf0)
                        * (ushT - 1.0) + Esh - 1.0)
                / (1.0 + Esh * ushT * 1.55 * (r_s ** 2 / R ** 2)
                   * (1.0 - 1.53 * delf0))
            )
        else:
            a, b = v['a'], v['b']
            K1 = 0.535 * math.pi * R ** 2
            ab, piR2 = a * b, math.pi * R ** 2
            log_arg = (R * math.sqrt(math.pi)) / (2.14 * math.sqrt(a * b))
            Esh = (1.135 * (1.0 + (K1 * delf0) / (1.0 - delf0)
                    + (2.1 - 2.5 * delf0) * delf0)
                   / (1.0 + (2.1 - 2.5 * delf0) * delf0
                      + 0.39 * ushT * delf0 * (1.0 - delf0)))
            Esh2 = (
                (0.2726 * (piR2 / ab) * deld) / (
                    (1.0 - delf0) ** 2
                    * (1.0 + delf0 * (0.486 + 1.56 * math.log(log_arg))) ** 2
                    * (1.0 + Esh * ushT * 1.55 * (ab / piR2)
                       * (1.0 - 1.53 * delf0)))
            ) + (
                deld * (Esh * 1.56 * (ab / piR2) * (1.0 - 1.53 * delf0)
                        * (ushT - 1.0))
                / (1.0 + Esh * ushT * 1.55 * (ab / piR2)
                   * (1.0 - 1.53 * delf0))
            )
        tgdelE = Esh2 / Esh
        return {'E': float(Esh), 'eps2': float(Esh2), 'tgo': float(tgdelE)}


METHOD = FerriteMethod()

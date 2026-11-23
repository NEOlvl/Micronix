"""Общий контракт измерительного метода (ТЗ-2).

Каждый метод — модуль в этом пакете, публикующий экземпляр METHOD:

    Method: id, name, standard, inputs[] (имя, единицы, диапазон),
            validate(params) -> errors[],
            calculate(params, resonance) -> MethodResult { values, errors, warnings }
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


class CalculationError(Exception):
    """Контролируемая ошибка расчёта методом."""


class SolverError(CalculationError):
    """Численный решатель не сошёлся (Д-3: вместо значений по умолчанию)."""


@dataclass(frozen=True)
class MethodInput:
    """Описание входного параметра метода.

    Используется GUI для построения формы (ТЗ-7, ТЗ-9) и для
    автоматической валидации по диапазону.
    """

    name: str                                        # ключ в params
    label: str                                       # подпись в форме
    unit: str = ''                                   # единицы измерения
    bounds: Optional[Tuple[float, float]] = None     # [мин; макс] включительно
    default: Optional[float] = None                  # значение по умолчанию
    required: bool = True
    # 'manual' — вводится оператором; 'resonance' — берётся из АЧХ
    source: str = 'manual'
    # если задано — параметр актуален только для перечисленных вариантов
    variants: Optional[Tuple[str, ...]] = None


@dataclass
class MethodResult:
    """Результат расчёта метода (Д-1: структура, не строка)."""

    values: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class ResonanceChannels:
    """Параметры резонансных кривых резонатора без и с образцом.

    Частоты в Гц, амплитуды в дБ — формат результата data_processor.
    Поля *e — резонанс с образцом (fE, f1E, f2E, AE).
    """

    f0: Optional[float] = None
    f1: Optional[float] = None
    f2: Optional[float] = None
    a0: Optional[float] = None
    fe: Optional[float] = None
    f1e: Optional[float] = None
    f2e: Optional[float] = None
    ae: Optional[float] = None

    @staticmethod
    def _q(f0, f1, f2):
        if f0 is None or f1 is None or f2 is None or f2 <= f1:
            return None
        return f0 / (f2 - f1)

    @property
    def q0(self):
        return self._q(self.f0, self.f1, self.f2)

    @property
    def qe(self):
        return self._q(self.fe, self.f1e, self.f2e)

    @staticmethod
    def _get(r, *names):
        if r is None:
            return None
        for n in names:
            v = r.get(n) if isinstance(r, dict) else getattr(r, n, None)
            if v is not None:
                return float(v)
        return None

    @classmethod
    def from_pair(cls, empty, loaded=None):
        """Собрать из двух ResonanceParameters/dict'ов data_processor.

        empty — резонанс без образца (f0, f1, f2, a0);
        loaded — резонанс с образцом (те же поля -> fe, f1e, f2e, ae).
        """
        return cls(
            f0=cls._get(empty, 'f0'), f1=cls._get(empty, 'f1'),
            f2=cls._get(empty, 'f2'), a0=cls._get(empty, 'a0', 'A0'),
            fe=cls._get(loaded, 'fe', 'f0'), f1e=cls._get(loaded, 'f1e', 'f1'),
            f2e=cls._get(loaded, 'f2e', 'f2'), ae=cls._get(loaded, 'ae', 'a0', 'A0'))

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(**{k: (float(v) if v is not None else None)
                      for k, v in d.items() if k in cls.__dataclass_fields__})

    def require(self, *fields: str) -> List[str]:
        """Ошибки по отсутствующим/нечисловым полям резонанса."""
        return [f"Не задан параметр резонанса '{name}'"
                for name in fields if getattr(self, name) is None]


class Method:
    """Базовый класс метода измерений (ТЗ-2)."""

    id: str = ''
    name: str = ''
    standard: str = ''
    description: str = ''
    # категория для группировки в GUI ('Диэлектрики' / 'Ферриты')
    category: str = 'Диэлектрики'
    inputs: Sequence[MethodInput] = ()
    # варианты метода (id -> название), если метод имеет несколько схем расчёта
    variants: Optional[Dict[str, str]] = None
    # поля ResonanceChannels, необходимые для расчёта
    resonance_fields: Sequence[str] = ()

    def applicable_inputs(self, variant: Optional[str] = None
                          ) -> List[MethodInput]:
        """Входные параметры, актуальные для выбранного варианта."""
        if variant is None:
            return list(self.inputs)
        return [i for i in self.inputs
                if i.variants is None or variant in i.variants]

    def validate(self, params: Dict, variant: Optional[str] = None
                 ) -> List[str]:
        """Проверка параметров по описанию inputs[] (ТЗ-7).

        Возвращает список ошибок; пустой список — параметры валидны.
        """
        errors: List[str] = []
        for spec in self.applicable_inputs(variant):
            raw = params.get(spec.name)
            if isinstance(raw, str) and not raw.strip():
                raw = None            # пустое поле формы -> default
            if raw is None:
                raw = spec.default
            if raw is None:
                if spec.required:
                    errors.append(
                        f"Не задан параметр '{spec.label}' ({spec.name})")
                continue
            try:
                val = float(raw)
            except (TypeError, ValueError):
                errors.append(
                    f"Параметр '{spec.label}' должен быть числом: {raw!r}")
                continue
            if spec.bounds is not None:
                lo, hi = spec.bounds
                if not (lo <= val <= hi):
                    errors.append(
                        f"Параметр '{spec.label}' = {val:g} {spec.unit} вне "
                        f"допустимого диапазона [{lo:g}; {hi:g}]")
        return errors

    def get_values(self, params: Dict, variant: Optional[str] = None
                   ) -> Dict[str, float]:
        """Числовые значения параметров с подстановкой default."""
        values = {}
        for spec in self.applicable_inputs(variant):
            raw = params.get(spec.name)
            if isinstance(raw, str) and not raw.strip():
                raw = None
            if raw is None:
                raw = spec.default
            values[spec.name] = float(raw) if raw is not None else None
        return values

    def calculate(self, params: Dict,
                  resonance: ResonanceChannels) -> MethodResult:
        """Выполнить расчёт. Переопределяется в модуле метода."""
        raise NotImplementedError

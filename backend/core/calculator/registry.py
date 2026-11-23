"""Реестр методов измерений (ТЗ-3).

GUI, генератор протоколов и прочие потребители получают список и
описание методов только отсюда. Добавление нового метода = новый
модуль с METHOD + строка в _METHOD_MODULES, без правки остального кода.
"""

from typing import Dict, List, Optional

from .base import Method
from .ferrite import METHOD as _FERRITE
from .mfd import METHOD as _MFD
from .mfch import METHOD as _MFCH
from .msr9 import METHOD as _MSR9
from .rod import METHOD as _ROD

_METHOD_MODULES = (_MFCH, _MFD, _ROD, _FERRITE, _MSR9)

METHODS: Dict[str, Method] = {m.id: m for m in _METHOD_MODULES}

# Соответствие старых числовых идентификаторов GUI (1-4) методам реестра
LEGACY_ID_MAP = {1: 'mfch', 2: 'mfd', 3: 'so', 4: 'svchf'}


def list_methods() -> List[Method]:
    """Все зарегистрированные методы в порядке реестра."""
    return list(_METHOD_MODULES)


def get_method(method_id) -> Optional[Method]:
    """Метод по id реестра или старому числовому идентификатору.

    Возвращает None, если метод не найден.
    """
    if isinstance(method_id, Method):
        return method_id
    if method_id in LEGACY_ID_MAP:
        method_id = LEGACY_ID_MAP[method_id]
    return METHODS.get(str(method_id))

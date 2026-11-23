from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List
import json


@dataclass
class SampleResult:
    name: str
    fe: float
    AE: float
    E: float = 0.0
    tgo: float = 0.0
    q_factor: float = 0.0
    raw_data: Dict[str, List[float]] = field(default_factory=dict)


@dataclass
class Measurement:
    id: str
    title: str
    method: str  # id метода из реестра backend.core.calculator
    date: datetime
    parameters: Dict[str, Any]

    # Данные резонатора без образца
    f0: float = 0.0
    f1: float = 0.0
    f2: float = 0.0
    A0: float = 0.0
    Q0: float = 0.0
    raw_data: Dict[str, List[float]] = field(default_factory=dict)

    # Образцы
    samples: Dict[str, SampleResult] = field(default_factory=dict)

    # Результаты
    results_calculated: bool = False

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'method': self.method,
            'date': self.date.isoformat(),
            'parameters': self.parameters,
            'f0': self.f0, 'f1': self.f1, 'f2': self.f2,
            'A0': self.A0, 'Q0': self.Q0,
            'samples': {k: vars(v) for k, v in self.samples.items()}
        }

    @property
    def method_obj(self):
        """Метод реестра backend.core.calculator или None."""
        from backend.core.calculator import get_method
        return get_method(self.method)

    @classmethod
    def from_dict(cls, data: Dict):
        method = data['method']
        # совместимость со старыми числовыми идентификаторами (1-4)
        if isinstance(method, int):
            from backend.core.calculator.registry import LEGACY_ID_MAP
            method = LEGACY_ID_MAP.get(method, str(method))
        return cls(
            id=data['id'],
            title=data['title'],
            method=str(method),
            date=datetime.fromisoformat(data['date']),
            parameters=data['parameters'],
            f0=data.get('f0', 0),
            f1=data.get('f1', 0),
            f2=data.get('f2', 0),
            A0=data.get('A0', 0),
            Q0=data.get('Q0', 0),
            samples={k: SampleResult(**v) for k, v in data.get('samples', {}).items()}
        )
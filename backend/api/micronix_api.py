"""Сервисный слой между GUI и backend (ТЗ-7, ТЗ-9).

Единственная точка входа интерфейса: реестр методов, формы по
inputs[], валидация параметров, сессия измерения с контролем
последовательности оператора и программными блокировками,
сохранение в SQLite, генерация PDF.

Сессия измерения (конечный автомат):

    idle  --measure_base()-->  base_done  --measure_sample()-->  base_done
    base_done --finish()--> finished   (нужен >= 1 образец)

Блокировки ТЗ-7: повторный съём базы, образец до базовой АЧХ,
завершение без образцов — SessionStateError.
"""

import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.core.calculator.base import (
    Method, MethodResult, ResonanceChannels)
from backend.core.calculator.registry import get_method, list_methods
from backend.core.report_generator import ReportGenerator
from backend.core.vna_controller import (
    SimulatedMode, SimulatorConfig, SimulatedVNA, VNAController,
    create_vna)
from backend.database.db_manager import DatabaseManager


class APIError(Exception):
    """Контролируемая ошибка сервисного слоя."""


class ParamsError(APIError):
    """Невалидные параметры метода (ТЗ-7)."""

    def __init__(self, errors: List[str]):
        self.errors = list(errors)
        super().__init__('; '.join(errors))


class SessionStateError(APIError):
    """Нарушена последовательность действий оператора (ТЗ-7)."""


@dataclass
class SampleRecord:
    """Результат измерения одного образца."""

    name: str
    sweep_y: List[float]
    resonance: Dict          # fe, f1e, f2e, ae, qe из data_processor
    result: MethodResult     # values, errors, warnings


class MeasurementSession:
    """Одна сессия измерения: базовая АЧХ + образцы -> запись в БД.

    Использует VNA через api — реальный контроллер или симулятор
    (тот же интерфейс, ТЗ-4). Для симулятора образцовая АЧХ снимается
    на симуляторе со смещённой модой (образец сдвигает резонанс).
    """

    def __init__(self, api: 'MicronixAPI', method: Method,
                 params: Dict[str, float], variant: Optional[str],
                 title: str = ''):
        self.api = api
        self.method = method
        self.params = dict(params)
        if variant:
            self.params['variant'] = variant
        self.variant = variant
        self.title = title
        self.id = uuid.uuid4().hex[:22]
        self.state = 'idle'
        self.base: Optional[Dict] = None      # sweep + resonance без образца
        self.samples: List[SampleRecord] = []

    # --- шаги оператора ---

    def measure_base(self) -> Dict:
        """Снять АЧХ пустого резонатора и выделить резонанс."""
        if self.state != 'idle':
            raise SessionStateError(
                'АЧХ без образца уже снята — повторный запуск '
                'требует новой сессии')
        vna = self.api.vna
        sweep = vna.measure_frequency_response()
        res = vna.find_resonance_parameters(
            sweep['frequencies'], sweep['amplitudes'])
        self.base = {'sweep': sweep, 'resonance': res}
        self.state = 'base_done'
        return res

    def measure_sample(self, name: str) -> SampleRecord:
        """Снять АЧХ с образцом и посчитать результат метода."""
        if self.state != 'base_done':
            raise SessionStateError(
                'Образец можно измерить только после АЧХ '
                'без образца')
        vna = self.api.vna_sample
        sweep = vna.measure_frequency_response()
        res = vna.find_resonance_parameters(
            sweep['frequencies'], sweep['amplitudes'])
        ch = ResonanceChannels.from_pair(
            self.base['resonance'], res)
        result = self.method.calculate(self.params, ch)
        sample = SampleRecord(
            name=name or f'Образец {len(self.samples) + 1}',
            sweep_y=list(sweep['amplitudes']),
            resonance={
                'fe': res.get('f0'), 'f1e': res.get('f1'),
                'f2e': res.get('f2'), 'ae': res.get('a0'),
                'qe': res.get('Q')},
            result=result)
        self.samples.append(sample)
        return sample

    def finish(self) -> str:
        """Сохранить сессию в БД. Возвращает measure_id."""
        if self.state != 'base_done':
            raise SessionStateError('Сессия ещё не содержит АЧХ')
        if not self.samples:
            raise SessionStateError(
                'Нельзя завершить измерение без образцов')
        record = self.to_record()
        measure_id = self.api.db.save_measurement(record)
        self.state = 'finished'
        return measure_id

    # --- сериализация ---

    def to_record(self) -> Dict:
        """Запись в формате db_manager."""
        res = self.base['resonance'] if self.base else {}
        sweep = self.base['sweep'] if self.base else {}
        samples = []
        for s in self.samples:
            e_val = s.result.values.get('E')
            samples.append({
                'name': s.name,
                'fe': s.resonance.get('fe'),
                'f1e': s.resonance.get('f1e'),
                'f2e': s.resonance.get('f2e'),
                'ae': s.resonance.get('ae'),
                'qe': s.resonance.get('qe'),
                'e': e_val, 'tgo': s.result.values.get('tgo'),
                'sweep_y': s.sweep_y,
                'values': dict(s.result.values),
                'errors': list(s.result.errors),
                'warnings': list(s.result.warnings),
            })
        return {
            'measure_id': self.id,
            'method_id': self.method.id,
            'title': self.title or self.id,
            'params': self.params,
            'f0': res.get('f0'), 'f1': res.get('f1'),
            'f2': res.get('f2'), 'a0': res.get('a0'),
            'q0': res.get('Q'),
            'sweep': {'x': list(sweep.get('frequencies') or []),
                      'y': list(sweep.get('amplitudes') or [])},
            'samples': samples,
        }


class MicronixAPI:
    """Фасад backend для GUI (ТЗ-9) и скриптов.

    simulate=True — симулятор ВАЦ (обязательный режим без железа).
    vna — можно передать свой контроллер/симулятор.
    """

    def __init__(self, db_path: str = 'data_base/micronix.db',
                 vna: Optional[VNAController] = None,
                 simulate: bool = True,
                 report_dir: str = 'report'):
        self.db = DatabaseManager(db_path)
        self.vna = vna or create_vna(simulate=simulate)
        self.vna_sample = (self._make_sample_vna(self.vna)
                           if isinstance(self.vna, SimulatedVNA)
                           else self.vna)
        self.reporter = ReportGenerator(report_dir)
        self.sessions: Dict[str, MeasurementSession] = {}
        self._connected = False

    # --- прибор ---

    def _ensure_connected(self):
        if not self._connected:
            self.vna.connect()
            if self.vna_sample is not self.vna:
                self.vna_sample.connect()
            self._connected = True

    @staticmethod
    def _make_sample_vna(base_vna: SimulatedVNA) -> SimulatedVNA:
        """Симулятор АЧХ с образцом: резонанс смещён вниз и ослаблен."""
        src = base_vna.sim

        def shifted(m: SimulatedMode) -> SimulatedMode:
            return SimulatedMode(
                f0=m.f0 * 0.999,          # образец сдвигает резонанс вниз
                q=m.q * 0.62,             # добротность падает (потери)
                depth_db=m.depth_db * 0.8)

        sim = SimulatorConfig(
            n_points=src.n_points, baseline_db=src.baseline_db,
            slope_db=src.slope_db, noise_db=src.noise_db,
            seed=None if src.seed is None else src.seed + 1,
            main_mode=shifted(src.main_mode),
            extra_modes=tuple(shifted(m) for m in src.extra_modes))
        return SimulatedVNA(config=base_vna.config, sim=sim)

    # --- методы ---

    def list_methods(self) -> List[Dict]:
        """Метаданные методов для карточек GUI (ТЗ-3, ТЗ-9)."""
        return [{
            'id': m.id, 'name': m.name, 'standard': m.standard,
            'description': m.description, 'category': m.category,
            'variants': m.variants,
        } for m in list_methods()]

    def method_form(self, method_id, variant: Optional[str] = None
                    ) -> Dict:
        """Описание формы ввода по inputs[] метода (ТЗ-9)."""
        method = get_method(method_id)
        if method is None:
            raise APIError(f'Неизвестный метод: {method_id!r}')
        return {
            'id': method.id, 'name': method.name,
            'standard': method.standard, 'variants': method.variants,
            'inputs': [{
                'name': i.name, 'label': i.label, 'unit': i.unit,
                'bounds': i.bounds, 'default': i.default,
                'required': i.required,
            } for i in method.applicable_inputs(variant)],
        }

    def validate_params(self, method_id, params: Dict,
                        variant: Optional[str] = None) -> List[str]:
        """Ошибки параметров по inputs[] (ТЗ-7). Пусто — валидно."""
        method = get_method(method_id)
        if method is None:
            return [f'Неизвестный метод: {method_id!r}']
        return method.validate(params, variant)

    # --- сессия измерения ---

    def start_measurement(self, method_id, params: Dict,
                          title: str = '',
                          variant: Optional[str] = None
                          ) -> MeasurementSession:
        """Создать сессию. Невалидные параметры -> ParamsError."""
        method = get_method(method_id)
        if method is None:
            raise APIError(f'Неизвестный метод: {method_id!r}')
        errors = method.validate(params, variant)
        if errors:
            raise ParamsError(errors)
        self._ensure_connected()
        session = MeasurementSession(
            self, method, method.get_values(params, variant),
            variant, title)
        self.sessions[session.id] = session
        return session

    # --- хранилище ---

    def list_measurements(self, method_id=None) -> List[Dict]:
        return self.db.list_measurements(method_id)

    def load_measurement(self, measure_id) -> Optional[Dict]:
        return self.db.load_measurement(measure_id)

    def generate_report(self, measure_id) -> str:
        record = self.db.load_measurement(measure_id)
        if record is None:
            raise APIError(f'Измерение не найдено: {measure_id!r}')
        return self.reporter.generate(record)

    # --- совместимость со страницами GUI (архивный формат) ---

    @staticmethod
    def record_to_display(record: Dict) -> Dict:
        """Запись БД -> формат отображения (как measurement_data)."""
        sweep = record.get('sweep') or {}
        y_samples = {}
        for i, s in enumerate(record.get('samples') or [], 1):
            y_samples[str(i)] = {
                'name': s.get('name'),
                'y_res': s.get('sweep_y') or sweep.get('y') or [],
                'fe': s.get('fe'), 'AE': s.get('ae'),
                'E': s.get('e'), 'tgo': s.get('tgo'),
            }
        return {
            'id_m': record.get('measure_id'),
            'title': record.get('title') or record.get('measure_id'),
            'method_id': record.get('method_id'),
            'time': record.get('created_at', ''),
            'x': sweep.get('x') or [],
            'y_res': sweep.get('y') or [],
            'y_samples': y_samples,
        }

    def query(self, command: str, params=None):
        """Совместимость с вызовами GUI-страниц.

        measure_data -> список записей в формате отображения;
        read_data    -> запись по id_m;
        generate_pdf -> путь к PDF.
        """
        params = params or {}
        if command == 'measure_data':
            return [self.record_to_display(self.db.load_measurement(m['measure_id']))
                    for m in self.db.list_measurements()]
        if command == 'read_data':
            rec = self.db.load_measurement(str(params.get('id_m') or ''))
            return self.record_to_display(rec) if rec else {}
        if command == 'generate_pdf':
            return self.generate_report(str(params.get('id_m') or ''))
        raise APIError(f'Неизвестная команда API: {command!r}')

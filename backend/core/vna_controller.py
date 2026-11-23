"""Контроллер ВАЦ и симулятор измерений (ТЗ-4, ТЗ-10).

VNAController — единственная точка обмена с прибором по SCPI:
    SENS:FREQ:STAR / SENS:FREQ:STOP   — установка диапазона
    CALC1:DATA:XAXis?               — ось частот
    CALC1:DATA:FDAT?                — АЧХ (пары значений, берётся каждое 2-е)

SimulatedVNA реализует тот же интерфейс без железа: переопределяет
только connect/write/query, поэтому весь путь разбора ответов и
валидации общий и тестируется на симуляторе.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.core.data_processor import extract_resonance_db


class VNAError(Exception):
    """Контролируемая ошибка обмена с векторным анализатором."""


@dataclass
class VNAConfig:
    address: str = "TCPIP0::localhost::5025::SOCKET"
    timeout: int = 500
    start_freq: float = 8e9   # Гц
    stop_freq: float = 12e9   # Гц


class VNAController:
    """Работа с векторным анализатором цепей по SCPI."""

    def __init__(self, config: Optional[VNAConfig] = None):
        self.config = config or VNAConfig()
        self._rm = None
        self.resource = None

    # --- подключение ---

    def _resource_manager(self):
        """Ленивая инициализация: pyvisa нужен только при реальном
        подключении, импорт модуля прибора не требует (ТЗ-11)."""
        if self._rm is None:
            import pyvisa
            self._rm = pyvisa.ResourceManager()
        return self._rm

    @property
    def is_connected(self) -> bool:
        return self.resource is not None

    def connect(self) -> bool:
        """Открыть соединение с прибором. При сбое — VNAError."""
        try:
            res = self._resource_manager().open_resource(
                self.config.address, timeout=self.config.timeout)
            res.read_termination = '\n'
            res.write_termination = '\n'
        except Exception as exc:
            raise VNAError(
                f"Не удалось подключиться к ВАЦ "
                f"({self.config.address}): {exc}") from exc
        self.resource = res
        return True

    def disconnect(self):
        """Закрыть соединение (идемпотентно)."""
        if self.resource is not None:
            try:
                self.resource.close()
            finally:
                self.resource = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.disconnect()
        return False

    # --- SCPI-транспорт ---

    def write(self, command: str):
        if not self.is_connected:
            raise VNAError("ВАЦ не подключен")
        try:
            self.resource.write(command)
        except Exception as exc:
            raise VNAError(f"Сбой записи '{command}': {exc}") from exc

    def query(self, command: str) -> str:
        if not self.is_connected:
            raise VNAError("ВАЦ не подключен")
        try:
            return self.resource.query(command)
        except Exception as exc:
            raise VNAError(f"Сбой запроса '{command}': {exc}") from exc

    # --- измерение ---

    def measure_frequency_response(self) -> Dict[str, List[float]]:
        """Снять АЧХ в заданном диапазоне.

        Returns:
            {'frequencies': [Гц...], 'amplitudes': [дБ...]}

        Raises:
            VNAError: нет соединения, повреждённый ответ прибора,
                      рассогласование длин массивов.
        """
        self.write(f"SENS:FREQ:STAR {self.config.start_freq:.9g}")
        self.write(f"SENS:FREQ:STOP {self.config.stop_freq:.9g}")
        freq_raw = self.query("CALC1:DATA:XAXis?")
        amp_raw = self.query("CALC1:DATA:FDAT?")

        frequencies = self._parse_csv(freq_raw, 'оси частот')
        amplitudes = self._parse_fdat(amp_raw)
        self._validate_sweep(frequencies, amplitudes)
        return {'frequencies': frequencies, 'amplitudes': amplitudes}

    @staticmethod
    def _parse_csv(raw: str, what: str) -> List[float]:
        """Разбор CSV-ответа прибора в список float с диагностикой."""
        raw = (raw or '').strip()
        if not raw:
            raise VNAError(f"Пустой ответ прибора для {what}")
        try:
            return [float(v) for v in raw.split(',') if v.strip()]
        except ValueError as exc:
            raise VNAError(
                f"Нечисловые данные в ответе прибора для {what}: "
                f"{raw[:80]!r}") from exc

    def _parse_fdat(self, raw: str) -> List[float]:
        """Амплитуды из ответа FDAT?: пары значений, каждое второе."""
        values = self._parse_csv(raw, 'АЧХ (FDAT)')
        if len(values) % 2:
            raise VNAError(
                f"Ответ FDAT? содержит нечётное число значений "
                f"({len(values)}) — формат пар нарушен")
        return values[::2]

    @staticmethod
    def _validate_sweep(frequencies: List[float],
                        amplitudes: List[float]):
        """Контроль ответа прибора (ТЗ-10): длины и конечность."""
        n_f, n_a = len(frequencies), len(amplitudes)
        if n_f != n_a:
            raise VNAError(
                f"Рассогласование длин массивов: частот {n_f}, "
                f"амплитуд {n_a}")
        if n_f < 16:
            raise VNAError(
                f"Слишком мало точек в свипе: {n_f} (нужно >= 16)")
        if not (np.isfinite(frequencies).all()
                and np.isfinite(amplitudes).all()):
            raise VNAError("Ответ прибора содержит NaN или Inf")

    def find_resonance_parameters(self, frequencies, amplitudes):
        """Параметры резонанса АЧХ (ТЗ-5, backend.core.data_processor)."""
        return extract_resonance_db(frequencies, amplitudes)


# ---------------------------------------------------------------------
# Симулятор (ТЗ-4): тот же интерфейс, синтетическая АЧХ
# ---------------------------------------------------------------------

@dataclass
class SimulatedMode:
    """Один резонансный провал синтетической АЧХ."""
    f0: float          # Гц
    q: float           # добротность
    depth_db: float    # глубина относительно базы, дБ


@dataclass
class SimulatorConfig:
    """Параметры синтетической АЧХ симулятора."""
    n_points: int = 1601
    baseline_db: float = -5.0        # базовый уровень в середине, дБ
    slope_db: float = -1.5           # наклон базы на весь диапазон, дБ
    noise_db: float = 0.3            # СКО шума, дБ
    seed: Optional[int] = 42
    # основной провал + боковые моды (реальные АЧХ многомодовы)
    main_mode: SimulatedMode = field(
        default_factory=lambda: SimulatedMode(10e9, 400.0, 30.0))
    extra_modes: Tuple[SimulatedMode, ...] = field(
        default_factory=lambda: (
            SimulatedMode(9.4e9, 900.0, 15.0),
            SimulatedMode(11.2e9, 700.0, 20.0),
        ))


class SimulatedVNA(VNAController):
    """Симулятор ВАЦ: синтетическая АЧХ без железа (ТЗ-4).

    Наследует разбор и валидацию ответов VNAController; подменяет
    только транспорт (connect/write/query). Генерирует многомодовую
    АЧХ в линейной мощности с наклонной базой и дБ-шумом — как
    реальные свипы из measurement_data.
    """

    def __init__(self, config: Optional[VNAConfig] = None,
                 sim: Optional[SimulatorConfig] = None):
        super().__init__(config)
        self.sim = sim or SimulatorConfig()
        self._connected = False
        self._freq_start = self.config.start_freq
        self._freq_stop = self.config.stop_freq

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def write(self, command: str):
        if not self._connected:
            raise VNAError("Симулятор не подключен")
        freq = self._parse_freq_command(command)
        if freq is not None:
            name, value = freq
            if name == 'STAR':
                self._freq_start = value
            else:
                self._freq_stop = value

    def query(self, command: str) -> str:
        if not self._connected:
            raise VNAError("Симулятор не подключен")
        cmd = command.strip().upper()
        if cmd == '*IDN?':
            return 'Micronix,VNA-SIM,0,1.0'
        if cmd == 'CALC1:DATA:XAXIS?':
            return ','.join(f'{v:.6e}' for v in self._freq_axis())
        if cmd == 'CALC1:DATA:FDAT?':
            amps = self._synth_amplitudes(self._freq_axis())
            # формат прибора: пары значений, амплитуда — каждое второе
            return ','.join(f'{v:.6e},0.0' for v in amps)
        raise VNAError(f"Симулятор: неизвестная команда '{command}'")

    # --- генерация ---

    _FREQ_CMD = re.compile(
        r'SENS:FREQ:(STAR|STOP)\s+([\d.eE+-]+)\s*(HZ|KHZ|MHZ|GHZ)?',
        re.IGNORECASE)
    _UNIT = {'HZ': 1.0, 'KHZ': 1e3, 'MHZ': 1e6, 'GHZ': 1e9}

    def _parse_freq_command(self, command: str):
        m = self._FREQ_CMD.match(command.strip())
        if not m:
            return None
        unit = self._UNIT.get((m.group(3) or 'HZ').upper(), 1.0)
        return m.group(1).upper(), float(m.group(2)) * unit

    def _freq_axis(self) -> np.ndarray:
        return np.linspace(self._freq_start, self._freq_stop,
                           self.sim.n_points)

    def _synth_amplitudes(self, f: np.ndarray) -> np.ndarray:
        """АЧХ в дБ: база с наклоном + лоренцевы провалы мод + шум."""
        s = self.sim
        fmid = 0.5 * (f[0] + f[-1])
        span = f[-1] - f[0]
        base_db = s.baseline_db + s.slope_db * (f - fmid) / span
        p = 10.0 ** (base_db / 10.0)
        for mode in (s.main_mode,) + tuple(s.extra_modes):
            depth_frac = 1.0 - 10.0 ** (-mode.depth_db / 10.0)
            lorentz = 1.0 / (1.0 + (2.0 * (f - mode.f0) * mode.q
                                    / mode.f0) ** 2)
            p = p * (1.0 - depth_frac * lorentz)
        a = 10.0 * np.log10(np.maximum(p, 1e-12))
        if s.noise_db > 0:
            a = a + np.random.default_rng(s.seed).normal(
                0.0, s.noise_db, f.size)
        return a


def create_vna(simulate: bool = False,
               config: Optional[VNAConfig] = None,
               sim: Optional[SimulatorConfig] = None) -> VNAController:
    """Фабрика: реальный контроллер либо симулятор (ТЗ-4).

    Вызывающий код не меняется — интерфейс идентичен.
    """
    if simulate:
        return SimulatedVNA(config, sim)
    return VNAController(config)

"""SQLite-хранилище измерений (ТЗ-8).

Хранит: метод, параметры, резонансные значения, сырые массивы АЧХ
(без образца и по каждому образцу), результаты, метки времени.
Сырые массивы позволяют повторно обработать сохранённые кривые
(data_processor + метод реестра).

Формат записи (dict):

    record = {
        'measure_id': 'uuid', 'method_id': 'mfd',
        'title': '...', 'description': '...',
        'params': {'t': 1.0, 'D': 45.0, ...},
        'f0': ..., 'f1': ..., 'f2': ..., 'a0': ..., 'q0': ...,
        'sweep': {'x': [Гц], 'y': [дБ]},
        'samples': [{'name', 'fe', 'f1e', 'f2e', 'ae', 'qe',
                     'e', 'tgo', 'sweep_y': [...]}],
    }
"""

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.calculator.base import ResonanceChannels
from backend.core.calculator.registry import LEGACY_ID_MAP

DEFAULT_DB_PATH = 'data_base/micronix.db'

_SCHEMA = """
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measure_id TEXT UNIQUE NOT NULL,
    method_id TEXT NOT NULL,
    title TEXT,
    description TEXT,
    params_json TEXT NOT NULL DEFAULT '{}',
    f0 REAL, f1 REAL, f2 REAL, a0 REAL, q0 REAL,
    sweep_x_json TEXT,
    sweep_y_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measurement_fk INTEGER NOT NULL
        REFERENCES measurements(id) ON DELETE CASCADE,
    name TEXT,
    fe REAL, f1e REAL, f2e REAL, ae REAL, qe REAL,
    e REAL, tgo REAL,
    sweep_y_json TEXT,
    extra_json TEXT
);
"""


class DatabaseError(Exception):
    """Контролируемая ошибка хранилища."""


class _SharedConnection:
    """Обёртка общего соединения: `with` не закрывает его."""

    def __init__(self, con: sqlite3.Connection):
        self._con = con

    def __enter__(self) -> sqlite3.Connection:
        return self._con

    def __exit__(self, *exc):
        if exc[0] is None:
            self._con.commit()
        else:
            self._con.rollback()
        return False


class DatabaseManager:
    """CRUD-интерфейс к хранилищу измерений."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        self._shared_con: Optional[sqlite3.Connection] = None
        if self.db_path != ':memory:':
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        # :memory: живёт в пределах одного соединения — держим общее
        if self.db_path == ':memory:':
            if self._shared_con is None:
                self._shared_con = sqlite3.connect(':memory:')
                self._shared_con.execute('PRAGMA foreign_keys = ON')
            return _SharedConnection(self._shared_con)
        con = sqlite3.connect(self.db_path)
        con.execute('PRAGMA foreign_keys = ON')
        return con

    def _init_schema(self):
        with self._connect() as con:
            con.executescript(_SCHEMA)

    # --- запись ---

    def save_measurement(self, record: Dict) -> str:
        """Сохранить измерение (upsert по measure_id).

        Обязательные ключи: method_id. Остальные — по формату записи.
        Возвращает measure_id.
        """
        method_id = record.get('method_id')
        if not method_id:
            raise DatabaseError("В записи нет 'method_id'")
        measure_id = str(record.get('measure_id') or uuid.uuid4().hex[:22])
        now = datetime.now().isoformat(timespec='seconds')
        sweep = record.get('sweep') or {}

        with self._connect() as con:
            old = con.execute(
                'SELECT id, created_at FROM measurements WHERE measure_id = ?',
                (measure_id,)).fetchone()
            if old:
                row_id, created_at = old
                con.execute(
                    'DELETE FROM samples WHERE measurement_fk = ?', (row_id,))
                con.execute('DELETE FROM measurements WHERE id = ?', (row_id,))
            else:
                created_at = now
            cur = con.execute(
                """INSERT INTO measurements
                   (measure_id, method_id, title, description, params_json,
                    f0, f1, f2, a0, q0, sweep_x_json, sweep_y_json,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (measure_id, str(method_id),
                 record.get('title', ''), record.get('description', ''),
                 json.dumps(record.get('params') or {},
                            ensure_ascii=False),
                 record.get('f0'), record.get('f1'), record.get('f2'),
                 record.get('a0'), record.get('q0'),
                 json.dumps(sweep.get('x') or []),
                 json.dumps(sweep.get('y') or []),
                 created_at, now))
            fk = cur.lastrowid
            for s in record.get('samples') or []:
                known = {'name', 'fe', 'f1e', 'f2e', 'ae', 'qe',
                         'e', 'tgo', 'sweep_y'}
                con.execute(
                    """INSERT INTO samples
                       (measurement_fk, name, fe, f1e, f2e, ae, qe,
                        e, tgo, sweep_y_json, extra_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (fk, s.get('name'), s.get('fe'), s.get('f1e'),
                     s.get('f2e'), s.get('ae'), s.get('qe'),
                     s.get('e'), s.get('tgo'),
                     json.dumps(s.get('sweep_y') or []),
                     json.dumps({k: v for k, v in s.items()
                                if k not in known},
                               ensure_ascii=False)))
        return measure_id

    # --- чтение ---

    def load_measurement(self, measure_id: str) -> Optional[Dict]:
        """Полная запись включая сырые массивы АЧХ и образцы."""
        with self._connect() as con:
            m = con.execute(
                """SELECT id, measure_id, method_id, title, description,
                          params_json, f0, f1, f2, a0, q0,
                          sweep_x_json, sweep_y_json, created_at, updated_at
                   FROM measurements WHERE measure_id = ?""",
                (measure_id,)).fetchone()
            if not m:
                return None
            samples = con.execute(
                """SELECT name, fe, f1e, f2e, ae, qe, e, tgo,
                          sweep_y_json, extra_json
                   FROM samples WHERE measurement_fk = ? ORDER BY id""",
                (m[0],)).fetchall()
        record = {
            'measure_id': m[1], 'method_id': m[2], 'title': m[3],
            'description': m[4],
            'params': json.loads(m[5] or '{}'),
            'f0': m[6], 'f1': m[7], 'f2': m[8], 'a0': m[9], 'q0': m[10],
            'sweep': {'x': json.loads(m[11] or '[]'),
                      'y': json.loads(m[12] or '[]')},
            'created_at': m[13], 'updated_at': m[14],
            'samples': [],
        }
        for s in samples:
            sample = {
                'name': s[0], 'fe': s[1], 'f1e': s[2], 'f2e': s[3],
                'ae': s[4], 'qe': s[5], 'e': s[6], 'tgo': s[7],
                'sweep_y': json.loads(s[8] or '[]'),
            }
            sample.update(json.loads(s[9] or '{}'))
            record['samples'].append(sample)
        return record

    def list_measurements(self, method_id: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Dict]:
        """Список измерений (метаданные, без сырых массивов)."""
        sql = """SELECT measure_id, method_id, title, created_at
                 FROM measurements"""
        args: list = []
        if method_id:
            sql += ' WHERE method_id = ?'
            args.append(str(method_id))
        sql += ' ORDER BY created_at DESC'
        if limit:
            sql += ' LIMIT ?'
            args.append(int(limit))
        with self._connect() as con:
            rows = con.execute(sql, args).fetchall()
        return [{'measure_id': r[0], 'method_id': r[1],
                 'title': r[2], 'created_at': r[3]} for r in rows]

    def delete_measurement(self, measure_id: str) -> bool:
        """Удалить измерение и его образцы. True, если было удалено."""
        with self._connect() as con:
            cur = con.execute('DELETE FROM measurements WHERE measure_id = ?',
                              (measure_id,))
            return cur.rowcount > 0


def resonance_from_record(record: Dict) -> ResonanceChannels:
    """ResonanceChannels из записи (для повторной обработки, ТЗ-8)."""
    samples = record.get('samples') or []
    first = samples[0] if samples else {}
    return ResonanceChannels(
        f0=record.get('f0'), f1=record.get('f1'), f2=record.get('f2'),
        a0=record.get('a0'),
        fe=first.get('fe'), f1e=first.get('f1e'), f2e=first.get('f2e'),
        ae=first.get('ae'))


_PARAM_KEY = re.compile(r'data\[\d+\]\[([a-zA-Z_]+)\]')


def record_from_archive(path) -> Dict:
    """Импорт архивного файла measurement_data/*.txt (JSON) в запись.

    Ключи вида 'data[2][t]' нормализуются в 't' — имена inputs[] методов.
    Сырой data_param сохраняется под 'params_raw'.
    """
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    data_param = d.get('data_param') or {}
    params = {}
    for key, val in data_param.items():
        m = _PARAM_KEY.match(str(key))
        if m:
            params[m.group(1)] = num(val) if num(val) is not None else val
    method_raw = data_param.get('method')
    method_id = None
    if method_raw is not None:
        method_id = LEGACY_ID_MAP.get(int(float(method_raw)),
                                      str(method_raw))

    samples = []
    for _, s in sorted((d.get('y_samples') or {}).items(),
                       key=lambda kv: int(kv[0])):
        samples.append({
            'name': s.get('name'),
            'fe': num(s.get('fe')), 'ae': num(s.get('AE')),
            'e': num(s.get('E')), 'tgo': num(s.get('tgo')),
            'sweep_y': [num(v) for v in s.get('y_res') or []],
        })

    return {
        'measure_id': Path(path).stem,
        'method_id': method_id or 'unknown',
        'title': d.get('title') or Path(path).stem,
        'description': d.get('description') or '',
        'params': params,
        'params_raw': data_param,
        'f0': num(d.get('f0')), 'f1': num(d.get('f1')),
        'f2': num(d.get('f2')), 'a0': num(d.get('A0')),
        'sweep': {'x': [num(v) for v in d.get('x') or []],
                  'y': [num(v) for v in d.get('y_res') or []]},
        'samples': samples,
    }

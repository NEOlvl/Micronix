"""Тесты report_generator: PDF по каждому методу, Д-8."""

import os
import pytest

from backend.core.report_generator import ReportError, ReportGenerator
from backend.core.calculator.registry import list_methods
from backend.database.db_manager import record_from_archive

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), '..',
                           'measurement_data')


def make_record(**over):
    rec = {
        'measure_id': 'rep001',
        'method_id': 'mfd',
        'title': 'Тестовый_замер',
        'params': {'t': 1.0, 'D': 45.0, 'L0': 80.0},
        'f0': 1.0e10,
        'created_at': '2025-06-01T12:00:00',
        'samples': [
            {'name': 'Образец 1', 'fe': 9.8e9, 'e': 2.51234,
             'tgo': 0.00254},
            {'name': 'Образец 2', 'fe': 9.75e9, 'e': 2.6,
             'tgo': 0.003},
        ],
    }
    rec.update(over)
    return rec


@pytest.fixture
def gen(tmp_path):
    return ReportGenerator(str(tmp_path / 'report'))


def assert_pdf(path):
    assert os.path.exists(path)
    assert os.path.getsize(path) > 3000
    with open(path, 'rb') as fh:
        assert fh.read(5) == b'%PDF-'


class TestGenerate:
    @pytest.mark.parametrize('method_id',
                             [m.id for m in list_methods()])
    def test_pdf_per_method(self, gen, method_id):
        rec = make_record(method_id=method_id,
                          measure_id=f'rep_{method_id}')
        path = gen.generate(rec)
        assert_pdf(path)

    def test_out_path(self, gen, tmp_path):
        out = str(tmp_path / 'custom.pdf')
        assert gen.generate(make_record(), out_path=out) == out
        assert_pdf(out)

    def test_unknown_method_no_crash(self, gen):
        """Д-8: неизвестный метод не роняет генерацию."""
        path = gen.generate(make_record(method_id='unknown',
                                        measure_id='rep_unk'))
        assert_pdf(path)

    def test_no_measure_id_raises(self, gen):
        with pytest.raises(ReportError):
            gen.generate({'method_id': 'mfd'})

    def test_empty_samples(self, gen):
        path = gen.generate(make_record(samples=[],
                                        measure_id='rep_empty'))
        assert_pdf(path)


class TestFromArchive:
    def test_archive_record_to_pdf(self, gen):
        """Сквозной путь: архивный файл -> запись -> PDF."""
        files = [f for f in os.listdir(ARCHIVE_DIR)
                 if f.endswith('.txt')]
        assert files
        rec = record_from_archive(os.path.join(ARCHIVE_DIR, files[0]))
        rec['measure_id'] = 'rep_arch'
        path = gen.generate(rec)
        assert_pdf(path)

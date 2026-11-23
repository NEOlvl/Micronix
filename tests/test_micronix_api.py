"""Тесты MicronixAPI: реестр, валидация, сессия, блокировки (ТЗ-7,9)."""

import os
import pytest

from backend.api.micronix_api import (
    APIError, MicronixAPI, ParamsError, SessionStateError)

MFD_PARAMS = {'t': 1.0, 'D': 45.0, 'L0': 80.0}


@pytest.fixture
def api(tmp_path):
    return MicronixAPI(db_path=str(tmp_path / 'test.db'),
                       simulate=True,
                       report_dir=str(tmp_path / 'report'))


class TestMethodMeta:
    def test_list_methods(self, api):
        methods = api.list_methods()
        assert {m['id'] for m in methods} == {
            'mfch', 'mfd', 'so', 'svchf', 'msr9'}
        for m in methods:
            assert m['name'] and m['standard'] and m['category']

    def test_method_form(self, api):
        form = api.method_form('mfd')
        names = [i['name'] for i in form['inputs']]
        assert names == ['t', 'D', 'L0', 'p']
        assert form['inputs'][0]['bounds'] == (0.5, 6.0)

    def test_method_form_variant_filters(self, api):
        # у СВЧФ вариант square требует a,b
        form_sq = api.method_form('svchf', 'square')
        names_sq = {i['name'] for i in form_sq['inputs']}
        assert {'a', 'b'} <= names_sq
        form_st = api.method_form('svchf', 'st')
        names_st = {i['name'] for i in form_st['inputs']}
        assert 'a' not in names_st and 'b' not in names_st

    def test_method_form_unknown(self, api):
        with pytest.raises(APIError):
            api.method_form('nonexistent')


class TestValidation:
    def test_valid_params(self, api):
        assert api.validate_params('mfd', MFD_PARAMS) == []

    def test_out_of_range(self, api):
        errors = api.validate_params('mfd', {**MFD_PARAMS, 't': 99})
        assert any('диапазон' in e for e in errors)

    def test_non_numeric(self, api):
        errors = api.validate_params('mfd', {**MFD_PARAMS, 't': 'abc'})
        assert any('числом' in e for e in errors)

    def test_missing(self, api):
        errors = api.validate_params('mfd', {'t': 1.0})
        assert len(errors) >= 2

    def test_start_invalid_raises(self, api):
        with pytest.raises(ParamsError) as exc:
            api.start_measurement('mfd', {'t': 99})
        assert exc.value.errors

    def test_start_unknown_method(self, api):
        with pytest.raises(APIError):
            api.start_measurement('nope', {})


class TestSession:
    def test_full_flow(self, api):
        s = api.start_measurement('mfd', MFD_PARAMS, title='Тест')
        res = s.measure_base()
        assert 9e9 < res['f0'] < 11e9
        smp = s.measure_sample('Образец 1')
        assert smp.result.ok, smp.result.errors
        assert 'E' in smp.result.values
        mid = s.finish()
        loaded = api.load_measurement(mid)
        assert loaded['method_id'] == 'mfd'
        assert len(loaded['samples']) == 1
        assert loaded['samples'][0]['e'] == smp.result.values['E']

    def test_sample_before_base_locked(self, api):
        s = api.start_measurement('mfd', MFD_PARAMS)
        with pytest.raises(SessionStateError):
            s.measure_sample('x')

    def test_base_twice_locked(self, api):
        s = api.start_measurement('mfd', MFD_PARAMS)
        s.measure_base()
        with pytest.raises(SessionStateError):
            s.measure_base()

    def test_finish_without_samples_locked(self, api):
        s = api.start_measurement('mfd', MFD_PARAMS)
        s.measure_base()
        with pytest.raises(SessionStateError):
            s.finish()

    def test_multiple_samples(self, api):
        s = api.start_measurement('mfd', MFD_PARAMS)
        s.measure_base()
        s.measure_sample('o1')
        s.measure_sample('o2')
        assert len(s.samples) == 2
        mid = s.finish()
        assert len(api.load_measurement(mid)['samples']) == 2

    def test_report_generated(self, api, tmp_path):
        s = api.start_measurement('mfd', MFD_PARAMS, title='Отчёт')
        s.measure_base()
        s.measure_sample('o1')
        mid = s.finish()
        pdf = api.generate_report(mid)
        assert os.path.exists(pdf)
        assert os.path.getsize(pdf) > 3000


class TestQueryCompat:
    """Формат отображения для GUI-страниц (архивный JSON)."""

    def test_measure_data(self, api):
        s = api.start_measurement('mfd', MFD_PARAMS, title='Замер')
        s.measure_base()
        s.measure_sample('Образец А')
        mid = s.finish()

        data = api.query('measure_data')
        assert len(data) == 1
        rec = data[0]
        assert rec['id_m'] == mid
        assert len(rec['x']) == len(rec['y_res']) > 100
        sample = rec['y_samples']['1']
        assert sample['name'] == 'Образец А'
        assert 'E' in sample and 'tgo' in sample

    def test_read_data(self, api):
        s = api.start_measurement('mfd', MFD_PARAMS)
        s.measure_base()
        s.measure_sample('o1')
        mid = s.finish()
        rec = api.query('read_data', {'id_m': mid})
        assert rec['id_m'] == mid

    def test_read_missing(self, api):
        assert api.query('read_data', {'id_m': 'none'}) == {}

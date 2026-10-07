"""
Tests for the vectorised compute().

compute() evaluates whole columns at once. These tests check, for every
reference equation, every parameter and both out-of-range strategies, that it
returns what calling the scalar methods row by row returns: the same values,
the same NA rows, the same column dtype, the same element types and the same
exceptions.
"""

import contextlib
import inspect
import io
import math
import unittest
import warnings

import numpy as np
import pandas as pd

import pyspiro
from pyspiro import CRAPO_1981, GLI_2012, GLI_2017, KUSTER_2008, ALQEREM_2019
from pyspiro.src.reference import LMSReference, Reference

METRICS = ('percent', 'zscore', 'lln', 'uln')


def _cohort(n=48, seed=11, with_nan=False):
    """Ages 1-100 y with quarter-year, half-way, whole-year and 0.1/0.2-year values; some edge rows."""
    rng = np.random.default_rng(seed)
    age = rng.uniform(1, 100, n)
    k = np.arange(n) % 6
    age = np.where(k == 1, np.round(age * 4) / 4, age)
    age = np.where(k == 2, np.floor(age * 4) / 4 + 0.125, age)
    age = np.where(k == 3, np.floor(age), age)
    age = np.where(k == 4, np.round(age * 10) / 10, age)
    age = np.where(k == 5, np.round(age * 5) / 5, age)
    df = pd.DataFrame({
        'sex': rng.integers(0, 2, n),
        'age': age,
        'height': rng.uniform(80, 210, n),
        'value': rng.uniform(0.2, 6, n),
        'weight': rng.uniform(15, 130, n),
        'u': rng.random(n),
    }, index=['r%d' % i for i in range(n)])
    if with_nan:
        df.loc[df.index[::7], 'height'] = np.nan
        df.loc[df.index[3::11], 'value'] = np.nan
    return df


def _rowwise(eq, df, parameter, metric, value_col, ethnicity_col, weight_col, records=None):
    """compute() as it was before vectorisation: one scalar call per row."""
    if isinstance(eq, LMSReference):
        params = set(inspect.signature(eq.lms).parameters) | {'value'}
    else:
        params = {n for n, p in inspect.signature(getattr(eq, metric)).parameters.items()
                  if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)}
    method = getattr(eq, metric)
    values = []
    for row in (records if records is not None else df.to_dict('records')):
        kw = {'sex': int(row['sex']), 'age': float(row['age']), 'height': float(row['height']),
              'parameter': parameter}
        if 'ethnicity' in params:
            kw['ethnicity'] = int(row[ethnicity_col]) if ethnicity_col is not None else 0
        if 'weight' in params:
            kw['weight'] = float(row[weight_col])
        if 'value' in params:
            kw['value'] = float(row[value_col]) if value_col is not None else 0.0
        values.append(method(**kw))
    return pd.Series(values, index=df.index, dtype=None if values else float)


def _outcome(fn):
    try:
        with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)     # the scalar methods warn on invalid powers
            return fn()
    except Exception as e:  # noqa: BLE001 - the exception type is part of the behaviour
        return type(e)


def _instances():
    for name in sorted(dir(pyspiro)):
        cls = getattr(pyspiro, name)
        if inspect.isclass(cls) and issubclass(cls, Reference) and not inspect.isabstract(cls):
            if name == 'LOUW_1996':
                for spirometer in cls.Spirometer:
                    yield '%s[%s]' % (name, spirometer.name), cls(spirometer.value)
            else:
                yield name, cls()


class TestComputeMatchesScalarMethods(unittest.TestCase):

    def assertSameColumn(self, got, expected, label):
        if isinstance(expected, type):
            self.assertIs(got, expected, label)
            return
        self.assertNotIsInstance(got, type, label)
        self.assertEqual(got.dtype, expected.dtype, label)
        self.assertTrue(got.index.equals(expected.index), label)
        for i, (x, y) in enumerate(zip(got.tolist(), expected.tolist())):
            where = '%s row %d: %r vs %r' % (label, i, x, y)
            if y is pd.NA or y is None:
                self.assertIs(x, y, where)
                continue
            self.assertIs(type(x), type(y), where)
            if isinstance(y, complex):
                self.assertEqual(x, y, where)
            elif math.isnan(y):
                self.assertTrue(math.isnan(x), where)
            elif label.endswith('percent'):
                # rounded to 2 decimals: an ulp of the predicted value may move a half-way case
                self.assertAlmostEqual(x, y, delta=0.0100001, msg=where)
            else:
                self.assertAlmostEqual(x, y, delta=1e-12 * max(1.0, abs(y)), msg=where)

    def _check(self, name, eq, df):
        eth = getattr(type(eq), 'Ethnicity', None)
        ethnicity_col = None
        if eth is not None or name.startswith('LOUW'):
            codes = [e.value for e in eth] if eth is not None else [0, 1]
            df = df.assign(eth=np.asarray(codes)[(df['u'] * len(codes)).astype(int) % len(codes)])
            ethnicity_col = 'eth'
        records = df.to_dict('records')

        def compute(metrics):
            return eq.compute(df, parameter, value_col='value', ethnicity_col=ethnicity_col,
                              weight_col='weight', metrics=metrics)

        for parameter in type(eq).Parameters:
            for strategy in ('ignore', 'closest'):
                eq.set_strategy(strategy)
                together = _outcome(lambda: compute(METRICS))
                for metric in METRICS:
                    label = '%s %s %s %s' % (name, parameter.name, strategy, metric)
                    if isinstance(together, type):      # some metric raises: check each on its own
                        got = _outcome(lambda: compute((metric,))[metric])
                    else:
                        got = together[metric]
                    expected = _outcome(lambda: _rowwise(eq, df, parameter, metric, 'value',
                                                         ethnicity_col, 'weight', records))
                    self.assertSameColumn(got, expected, label)
        eq.set_strategy('ignore')

    def test_every_equation_matches_row_by_row(self):
        df = _cohort()
        for name, eq in _instances():
            with self.subTest(equation=name):
                self._check(name, eq, df)

    def test_missing_heights_and_values(self):
        df = _cohort(n=36, with_nan=True)
        for name, eq in _instances():
            with self.subTest(equation=name):
                self._check(name, eq, df)

    def test_zero_and_negative_values(self):
        # zscore() raises or returns complex numbers for these with some equations; compute() must too
        df = _cohort(n=24).assign(value=[0.0, -1.0, 2.0, 11.0] * 6)
        for name, eq in _instances():
            with self.subTest(equation=name):
                self._check(name, eq, df)


class TestComputeVectorisedBehaviour(unittest.TestCase):

    def test_empty_dataframe(self):
        empty = _cohort().iloc[:0]
        for eq, parameter in ((GLI_2017(), GLI_2017.Parameters.TLCO), (CRAPO_1981(), CRAPO_1981.Parameters.FVC)):
            result = eq.compute(empty, parameter, value_col='value')
            self.assertEqual(list(result.columns), list(METRICS))
            self.assertEqual(len(result), 0)

    def test_subclass_overriding_lms_is_used(self):
        class Halved(GLI_2017):
            def lms(self, sex, age, height, parameter, value):
                l, m, s = super().lms(sex, age, height, parameter, value)
                return l, (m / 2 if m is not pd.NA else m), s

        df = _cohort(n=20)
        got = Halved().compute(df, GLI_2017.Parameters.TLCO, value_col='value', metrics=('percent',))['percent']
        base = GLI_2017().compute(df, GLI_2017.Parameters.TLCO, value_col='value', metrics=('percent',))['percent']
        valid = ~base.isna()
        np.testing.assert_allclose(got[valid].astype(float), 2 * base[valid].astype(float), atol=0.011)

    def test_subclass_overriding_a_metric_is_used(self):
        class Constant(CRAPO_1981):
            def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None):
                return 42.0

        result = Constant().compute(_cohort(n=10), CRAPO_1981.Parameters.FVC, value_col='value')
        self.assertTrue((result['percent'] == 42.0).all())

    def test_kuster_parameter_without_equation_raises(self):
        df = _cohort(n=10).assign(age=50.0, height=170.0)
        with self.assertRaises(ValueError):
            KUSTER_2008().compute(df, KUSTER_2008.Parameters.FVC_LLN, value_col='value', metrics=('percent',))
        with self.assertRaises(ValueError):
            KUSTER_2008().compute(df, KUSTER_2008.Parameters.FVC, value_col='value', metrics=('lln',))

    def test_all_rows_out_of_range(self):
        df = _cohort(n=10).assign(age=5.0)
        result = ALQEREM_2019().compute(df, ALQEREM_2019.Parameters.FEV1, value_col='value')
        self.assertTrue(result.map(lambda v: v is pd.NA).all().all())

    def test_gli2012_equation_only_parameters(self):
        df = pd.DataFrame({'sex': [1, 0, 1, 0, 1], 'age': [5.1, 6.9, 7.5, 4.0, 5.0],
                           'height': [110.0, 115, 120, 100, 108], 'value': [1.0, 1.1, 1.2, 0.9, 1.0],
                           'eth': [1, 1, 1, 2, 5]})
        g = GLI_2012()
        for parameter in (GLI_2012.Parameters.FEV075, GLI_2012.Parameters.FEV075FVC):
            result = g.compute(df, parameter, value_col='value', ethnicity_col='eth', metrics=('zscore',))
            for i, row in df.iterrows():
                expected = g.zscore(int(row['sex']), row['age'], row['height'], int(row['eth']), parameter,
                                    row['value'])
                if expected is pd.NA:
                    self.assertIs(result['zscore'].iloc[i], pd.NA)
                else:
                    self.assertAlmostEqual(result['zscore'].iloc[i], expected, places=12)

    def test_gli2012_unknown_ethnicity_raises(self):
        df = _cohort(n=5).assign(age=40.0, height=175.0, eth=[1, 2, 9, 1, 1])
        with self.assertRaises(ValueError):
            GLI_2012().compute(df, GLI_2012.Parameters.FEV1, value_col='value', ethnicity_col='eth')

    def test_out_of_range_message_printed_once_per_row(self):
        g = GLI_2017()
        g.set_silence(False)
        df = _cohort(n=4).assign(age=[40.0, 3.0, 50.0, 95.5], height=170.0)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            g.compute(df, GLI_2017.Parameters.TLCO, value_col='value')
        self.assertEqual(out.getvalue().count('does not fit'), 2)


if __name__ == '__main__':
    unittest.main()

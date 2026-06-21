import math
import unittest
import pandas as pd
from pyspiro import JIAN_2017

M = 1
F = 0


class TestJian2017Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(JIAN_2017())

    def test_age_range(self):
        j = JIAN_2017()
        self.assertEqual(j._age_range, (4, 80))

    def test_parameters_enum(self):
        names = [p.name for p in JIAN_2017.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'PEF', 'MMEF'):
            self.assertIn(name, names)


class TestJian2017LMS(unittest.TestCase):

    def setUp(self):
        self.j = JIAN_2017()

    def test_lms_returns_three_floats_male(self):
        l, m, s = self.j.lms(M, 40, 170, JIAN_2017.Parameters.FEV1)
        self.assertIsInstance(l, float)
        self.assertIsInstance(m, float)
        self.assertIsInstance(s, float)

    def test_lms_returns_three_floats_female(self):
        l, m, s = self.j.lms(F, 40, 160, JIAN_2017.Parameters.FVC)
        self.assertIsInstance(l, float)
        self.assertIsInstance(m, float)
        self.assertIsInstance(s, float)

    def test_m_is_positive(self):
        for param in JIAN_2017.Parameters:
            with self.subTest(param=param.name):
                _, m, _ = self.j.lms(M, 40, 170, param)
                self.assertGreater(m, 0)

    def test_s_is_positive(self):
        for param in JIAN_2017.Parameters:
            with self.subTest(param=param.name):
                _, _, s = self.j.lms(M, 40, 170, param)
                self.assertGreater(s, 0)

    def test_male_differs_from_female(self):
        _, m_m, _ = self.j.lms(M, 40, 170, JIAN_2017.Parameters.FEV1)
        _, m_f, _ = self.j.lms(F, 40, 160, JIAN_2017.Parameters.FEV1)
        self.assertNotAlmostEqual(m_m, m_f, places=2)

    def test_all_parameters_valid_lms(self):
        for sex, ht in ((M, 170), (F, 160)):
            for param in JIAN_2017.Parameters:
                with self.subTest(sex=sex, param=param.name):
                    l, m, s = self.j.lms(sex, 40, ht, param)
                    self.assertFalse(pd.isna(m))
                    self.assertFalse(pd.isna(s))


# ── Table 3 cross-checks (adult predicted medians) ──────────────────────────
#
# Reference: Jian et al. 2017, Table 3.
#   Males:   170 cm; Females: 160 cm
#   Values reported as FVC (L), FEV1 (L), FEV1/FVC%

class TestJian2017AdultMaleTable3(unittest.TestCase):
    """Predicted medians for adult males at 170 cm (Table 3)."""

    def setUp(self):
        self.j = JIAN_2017()

    def _check(self, param, age, height, expected, tol=0.02):
        _, m, _ = self.j.lms(M, age, height, param)
        self.assertAlmostEqual(m, expected, delta=tol,
                               msg=f'{param.name} male age={age} h={height}: got {m:.3f}, expected {expected}')

    def test_fvc_20(self):  self._check(JIAN_2017.Parameters.FVC,     20, 170, 4.64)
    def test_fvc_40(self):  self._check(JIAN_2017.Parameters.FVC,     40, 170, 4.48)
    def test_fvc_60(self):  self._check(JIAN_2017.Parameters.FVC,     60, 170, 3.98)

    def test_fev1_20(self): self._check(JIAN_2017.Parameters.FEV1,    20, 170, 4.09)
    def test_fev1_40(self): self._check(JIAN_2017.Parameters.FEV1,    40, 170, 3.71)
    def test_fev1_60(self): self._check(JIAN_2017.Parameters.FEV1,    60, 170, 3.16)

    def test_fev1fvc_20(self): self._check(JIAN_2017.Parameters.FEV1FVC, 20, 170, 87.4, tol=0.1)
    def test_fev1fvc_40(self): self._check(JIAN_2017.Parameters.FEV1FVC, 40, 170, 83.0, tol=0.1)
    def test_fev1fvc_60(self): self._check(JIAN_2017.Parameters.FEV1FVC, 60, 170, 79.5, tol=0.1)


class TestJian2017AdultFemaleTable3(unittest.TestCase):
    """Predicted medians for adult females at 160 cm (Table 3)."""

    def setUp(self):
        self.j = JIAN_2017()

    def _check(self, param, age, height, expected, tol=0.02):
        _, m, _ = self.j.lms(F, age, height, param)
        self.assertAlmostEqual(m, expected, delta=tol,
                               msg=f'{param.name} female age={age} h={height}: got {m:.3f}, expected {expected}')

    def test_fvc_20(self):  self._check(JIAN_2017.Parameters.FVC,     20, 160, 3.42)
    def test_fvc_40(self):  self._check(JIAN_2017.Parameters.FVC,     40, 160, 3.39)
    def test_fvc_60(self):  self._check(JIAN_2017.Parameters.FVC,     60, 160, 2.96)

    def test_fev1_20(self): self._check(JIAN_2017.Parameters.FEV1,    20, 160, 3.08)
    def test_fev1_40(self): self._check(JIAN_2017.Parameters.FEV1,    40, 160, 2.80)
    def test_fev1_60(self): self._check(JIAN_2017.Parameters.FEV1,    60, 160, 2.33)

    def test_fev1fvc_20(self): self._check(JIAN_2017.Parameters.FEV1FVC, 20, 160, 90.4, tol=0.1)
    def test_fev1fvc_40(self): self._check(JIAN_2017.Parameters.FEV1FVC, 40, 160, 83.1, tol=0.1)
    def test_fev1fvc_60(self): self._check(JIAN_2017.Parameters.FEV1FVC, 60, 160, 78.8, tol=0.1)


# ── Table 4 cross-checks (children predicted medians) ───────────────────────
#
# Reference: Jian et al. 2017, Table 4.
#   Male children heights:   117 cm (6 y), 140 cm (10 y), 164 cm (14 y)
#   Female children heights: 117 cm (6 y), 141 cm (10 y), 158 cm (14 y)

class TestJian2017ChildrenMaleTable4(unittest.TestCase):

    def setUp(self):
        self.j = JIAN_2017()

    def _check(self, param, age, height, expected, tol=0.02):
        _, m, _ = self.j.lms(M, age, height, param)
        self.assertAlmostEqual(m, expected, delta=tol,
                               msg=f'{param.name} male age={age} h={height}: got {m:.3f}, expected {expected}')

    def test_fvc_6(self):   self._check(JIAN_2017.Parameters.FVC,  6,  117, 1.43)
    def test_fvc_10(self):  self._check(JIAN_2017.Parameters.FVC,  10, 140, 2.32)
    def test_fvc_14(self):  self._check(JIAN_2017.Parameters.FVC,  14, 164, 3.78)

    def test_fev1_6(self):  self._check(JIAN_2017.Parameters.FEV1, 6,  117, 1.29)
    def test_fev1_10(self): self._check(JIAN_2017.Parameters.FEV1, 10, 140, 2.03)
    def test_fev1_14(self): self._check(JIAN_2017.Parameters.FEV1, 14, 164, 3.32)

    def test_fev1fvc_6(self):  self._check(JIAN_2017.Parameters.FEV1FVC, 6,  117, 91.5, tol=0.1)
    def test_fev1fvc_10(self): self._check(JIAN_2017.Parameters.FEV1FVC, 10, 140, 88.6, tol=0.1)
    def test_fev1fvc_14(self): self._check(JIAN_2017.Parameters.FEV1FVC, 14, 164, 87.9, tol=0.1)


class TestJian2017ChildrenFemaleTable4(unittest.TestCase):

    def setUp(self):
        self.j = JIAN_2017()

    def _check(self, param, age, height, expected, tol=0.02):
        _, m, _ = self.j.lms(F, age, height, param)
        self.assertAlmostEqual(m, expected, delta=tol,
                               msg=f'{param.name} female age={age} h={height}: got {m:.3f}, expected {expected}')

    def test_fvc_6(self):   self._check(JIAN_2017.Parameters.FVC,  6,  117, 1.33)
    def test_fvc_10(self):  self._check(JIAN_2017.Parameters.FVC,  10, 141, 2.22)
    def test_fvc_14(self):  self._check(JIAN_2017.Parameters.FVC,  14, 158, 3.15)

    def test_fev1_6(self):  self._check(JIAN_2017.Parameters.FEV1, 6,  117, 1.22)
    def test_fev1_10(self): self._check(JIAN_2017.Parameters.FEV1, 10, 141, 1.99)
    def test_fev1_14(self): self._check(JIAN_2017.Parameters.FEV1, 14, 158, 2.89)

    def test_fev1fvc_6(self):  self._check(JIAN_2017.Parameters.FEV1FVC, 6,  117, 92.5, tol=0.1)
    def test_fev1fvc_10(self): self._check(JIAN_2017.Parameters.FEV1FVC, 10, 141, 90.8, tol=0.1)
    def test_fev1fvc_14(self): self._check(JIAN_2017.Parameters.FEV1FVC, 14, 158, 91.6, tol=0.1)


class TestJian2017Metrics(unittest.TestCase):

    def setUp(self):
        self.j = JIAN_2017()

    def test_percent_at_median_is_100(self):
        _, m, _ = self.j.lms(M, 40, 170, JIAN_2017.Parameters.FEV1)
        pct = self.j.percent(M, 40, 170, JIAN_2017.Parameters.FEV1, m)
        self.assertAlmostEqual(pct, 100.0, places=1)

    def test_zscore_at_median_is_zero(self):
        _, m, _ = self.j.lms(M, 40, 170, JIAN_2017.Parameters.FEV1)
        z = self.j.zscore(M, 40, 170, JIAN_2017.Parameters.FEV1, m)
        self.assertAlmostEqual(z, 0.0, places=3)

    def test_lln_below_median(self):
        lln = self.j.lln(M, 40, 170, JIAN_2017.Parameters.FEV1, 3.71)
        _, m, _ = self.j.lms(M, 40, 170, JIAN_2017.Parameters.FEV1)
        self.assertLess(lln, m)

    def test_uln_above_median(self):
        uln = self.j.uln(M, 40, 170, JIAN_2017.Parameters.FEV1, 3.71)
        _, m, _ = self.j.lms(M, 40, 170, JIAN_2017.Parameters.FEV1)
        self.assertGreater(uln, m)

    def test_lln_positive_for_all_parameters(self):
        for param in JIAN_2017.Parameters:
            with self.subTest(param=param.name):
                lln = self.j.lln(M, 40, 170, param, 0)
                self.assertFalse(pd.isna(lln))
                self.assertGreater(lln, 0)


class TestJian2017OutOfRange(unittest.TestCase):

    def setUp(self):
        self.j = JIAN_2017()

    def test_age_below_range_returns_na(self):
        l, m, s = self.j.lms(M, 3, 100, JIAN_2017.Parameters.FEV1)
        self.assertTrue(pd.isna(m))

    def test_age_above_range_returns_na(self):
        l, m, s = self.j.lms(M, 81, 175, JIAN_2017.Parameters.FEV1)
        self.assertTrue(pd.isna(m))

    def test_percent_out_of_range_returns_na(self):
        result = self.j.percent(M, 3, 100, JIAN_2017.Parameters.FEV1, 1.0)
        self.assertTrue(pd.isna(result))


class TestJian2017Compute(unittest.TestCase):

    def setUp(self):
        self.j = JIAN_2017()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 30.0],
            'height': [170.0, 160.0],
            'FEV1':   [3.71, 2.80],
        })

    def test_compute_returns_dataframe(self):
        result = self.j.compute(self.df, JIAN_2017.Parameters.FEV1,
                                value_col='FEV1', metrics=('percent', 'zscore', 'lln', 'uln'))
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

    def test_compute_columns_present(self):
        result = self.j.compute(self.df, JIAN_2017.Parameters.FEV1,
                                value_col='FEV1', metrics=('percent', 'zscore', 'lln', 'uln'))
        for col in ('percent', 'zscore', 'lln', 'uln'):
            self.assertIn(col, result.columns)


if __name__ == '__main__':
    unittest.main()

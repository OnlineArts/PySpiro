import unittest
import pandas as pd
from pyspiro import SLIMAN_1981

M = 1
F = 0
P = SLIMAN_1981.Parameters


class TestSliman1981Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(SLIMAN_1981())

    def test_age_range(self):
        self.assertEqual(SLIMAN_1981()._age_range, (20, 60))

    def test_height_range(self):
        self.assertEqual(SLIMAN_1981()._height_range, (140, 190))

    def test_parameters_enum(self):
        names = [p.name for p in SLIMAN_1981.Parameters]
        for name in ('FVC', 'FEV1', 'FEF25_75'):
            self.assertIn(name, names)


class TestSliman1981Predicted(unittest.TestCase):
    """
    Predicted values computed directly from the published linear equations
    (Sliman et al. 1981, Results section), e.g. male FVC = 0.059*h - 0.024*age - 4.171.
    The paper reports nomograms rather than worked numeric examples, so these
    reference values are derived from the equations themselves.
    """

    def setUp(self):
        self.s = SLIMAN_1981()

    def _check(self, sex, age, height, param, expected):
        self.assertAlmostEqual(self.s.predicted(sex, age, height, param), expected, places=3)

    # Males at 170 cm, 40 yr
    def test_male_fvc(self):   self._check(M, 40, 170, P.FVC,      4.8990)
    def test_male_fev1(self):  self._check(M, 40, 170, P.FEV1,     4.0570)
    def test_male_fmf(self):   self._check(M, 40, 170, P.FEF25_75, 3.7630)

    # Females at 160 cm, 40 yr
    def test_female_fvc(self):  self._check(F, 40, 160, P.FVC,      3.5840)
    def test_female_fev1(self): self._check(F, 40, 160, P.FEV1,     2.9160)
    def test_female_fmf(self):  self._check(F, 40, 160, P.FEF25_75, 2.7670)


class TestSliman1981Limits(unittest.TestCase):

    def setUp(self):
        self.s = SLIMAN_1981()

    def test_lln_male_fvc(self):
        self.assertAlmostEqual(self.s.lln(M, 40, 170, P.FVC), 3.9975, places=3)

    def test_uln_male_fvc(self):
        self.assertAlmostEqual(self.s.uln(M, 40, 170, P.FVC), 5.8005, places=3)

    def test_lln_female_fev1(self):
        self.assertAlmostEqual(self.s.lln(F, 40, 160, P.FEV1), 2.2958, places=3)

    def test_lln_below_predicted_uln_above(self):
        for sex, h in ((M, 170), (F, 160)):
            for p in SLIMAN_1981.Parameters:
                with self.subTest(sex=sex, param=p.name):
                    pred = self.s.predicted(sex, 40, h, p)
                    self.assertLess(self.s.lln(sex, 40, h, p), pred)
                    self.assertGreater(self.s.uln(sex, 40, h, p), pred)


class TestSliman1981Metrics(unittest.TestCase):

    def setUp(self):
        self.s = SLIMAN_1981()

    def test_percent(self):
        self.assertAlmostEqual(self.s.percent(M, 40, 170, P.FVC, 5.0), 102.06, places=2)

    def test_zscore(self):
        self.assertAlmostEqual(self.s.zscore(M, 40, 170, P.FVC, 5.0), 0.1843, places=3)

    def test_percent_at_predicted_is_100(self):
        pred = self.s.predicted(M, 40, 170, P.FEV1)
        self.assertAlmostEqual(self.s.percent(M, 40, 170, P.FEV1, pred), 100.0, places=2)

    def test_zscore_at_predicted_is_zero(self):
        pred = self.s.predicted(F, 40, 160, P.FVC)
        self.assertAlmostEqual(self.s.zscore(F, 40, 160, P.FVC, pred), 0.0, places=6)

    def test_lms_not_applicable(self):
        self.assertEqual(self.s.lms(M, 40, 170, P.FVC), (pd.NA, pd.NA, pd.NA))


class TestSliman1981OutOfRange(unittest.TestCase):

    def setUp(self):
        self.s = SLIMAN_1981()

    def test_age_below_range(self):
        self.assertTrue(pd.isna(self.s.predicted(M, 18, 170, P.FVC)))

    def test_age_above_range(self):
        self.assertTrue(pd.isna(self.s.predicted(M, 70, 170, P.FVC)))

    def test_height_below_range(self):
        self.assertTrue(pd.isna(self.s.predicted(M, 40, 130, P.FVC)))

    def test_height_above_range(self):
        self.assertTrue(pd.isna(self.s.predicted(M, 40, 200, P.FVC)))

    def test_percent_out_of_range(self):
        self.assertTrue(pd.isna(self.s.percent(M, 70, 170, P.FVC, 4.0)))

    def test_zscore_out_of_range(self):
        self.assertTrue(pd.isna(self.s.zscore(M, 70, 170, P.FVC, 4.0)))


class TestSliman1981ClosestStrategy(unittest.TestCase):

    def test_closest_clamps_age(self):
        s = SLIMAN_1981()
        s.set_strategy('closest')
        # age 70 clamps to 60; FVC male 170 cm, age 60
        expected = 0.059 * 170 - 0.024 * 60 - 4.171
        self.assertAlmostEqual(s.predicted(M, 70, 170, P.FVC), expected, places=3)


class TestSliman1981Compute(unittest.TestCase):

    def setUp(self):
        self.s = SLIMAN_1981()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 30.0],
            'height': [170.0, 160.0],
            'FVC':    [5.0, 3.5],
        })

    def test_compute_returns_dataframe(self):
        result = self.s.compute(self.df, P.FVC, value_col='FVC')
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

    def test_compute_columns_present(self):
        result = self.s.compute(self.df, P.FVC, value_col='FVC',
                                metrics=('percent', 'zscore', 'lln', 'uln'))
        for col in ('percent', 'zscore', 'lln', 'uln'):
            self.assertIn(col, result.columns)


if __name__ == '__main__':
    unittest.main()

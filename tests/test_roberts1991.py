import unittest
import pandas as pd
from pyspiro import ROBERTS_1991

M = 1
F = 0


class TestRoberts1991Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(ROBERTS_1991())

    def test_age_range(self):
        r = ROBERTS_1991()
        self.assertEqual(r._age_range, (18, 86))

    def test_height_ranges(self):
        r = ROBERTS_1991()
        self.assertEqual(r._HEIGHT_MALE_RANGE, (161.0, 196.0))
        self.assertEqual(r._HEIGHT_FEMALE_RANGE, (146.0, 177.0))

    def test_parameters_enum(self):
        params = [p.name for p in ROBERTS_1991.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'PEFR', 'FEF50'):
            self.assertIn(name, params)


class TestRoberts1991Percent(unittest.TestCase):

    def setUp(self):
        self.r = ROBERTS_1991()

    def test_known_fvc_male(self):
        result = self.r.percent(M, 40, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)
        self.assertAlmostEqual(result, 88.2, places=1)

    def test_all_parameters_return_float_male(self):
        for param in ROBERTS_1991.Parameters:
            with self.subTest(param=param.name):
                result = self.r.percent(M, 40, 175, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in ROBERTS_1991.Parameters:
            with self.subTest(param=param.name):
                result = self.r.percent(F, 40, 163, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        r_m = self.r.percent(M, 40, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)
        r_f = self.r.percent(F, 40, 163, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)
        self.assertNotAlmostEqual(r_m, r_f, places=1)

    def test_older_patient_gives_lower_predicted(self):
        # For same height, older patient → lower predicted FVC → higher percent for same value
        r_young = self.r.percent(M, 30, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)
        r_old = self.r.percent(M, 70, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)
        self.assertGreater(r_old, r_young)


class TestRoberts1991NoLLN(unittest.TestCase):

    def setUp(self):
        self.r = ROBERTS_1991()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.r.lln(M, 40, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.r.uln(M, 40, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.r.zscore(M, 40, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.5)))


class TestRoberts1991OutOfRange(unittest.TestCase):

    def setUp(self):
        self.r = ROBERTS_1991()

    def test_age_below_range_returns_na(self):
        result = self.r.percent(M, 17, 175, parameter=ROBERTS_1991.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.r.percent(M, 87, 175, parameter=ROBERTS_1991.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))

    def test_male_height_below_range_returns_na(self):
        result = self.r.percent(M, 40, 160, parameter=ROBERTS_1991.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_female_height_above_range_returns_na(self):
        result = self.r.percent(F, 40, 178, parameter=ROBERTS_1991.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

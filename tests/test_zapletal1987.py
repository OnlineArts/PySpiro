import unittest
import pandas as pd
from pyspiro import ZAPLETAL_1987

M = 1
F = 0


class TestZapletal1987Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(ZAPLETAL_1987())

    def test_age_range(self):
        z = ZAPLETAL_1987()
        self.assertEqual(z._age_range, (6, 18))

    def test_height_range(self):
        z = ZAPLETAL_1987()
        self.assertEqual(z._HEIGHT_RANGE, (107.0, 182.0))

    def test_parameters_enum(self):
        params = [p.name for p in ZAPLETAL_1987.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'FEF25', 'FEF50', 'FEF75',
                     'FEF25_75', 'PEFR', 'SVC', 'MVV'):
            self.assertIn(name, params)


class TestZapletal1987Percent(unittest.TestCase):

    def setUp(self):
        self.z = ZAPLETAL_1987()

    def test_known_fvc_male(self):
        result = self.z.percent(M, 12, 150, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)
        self.assertAlmostEqual(result, 85.61, places=1)

    def test_all_parameters_return_float_male(self):
        for param in ZAPLETAL_1987.Parameters:
            with self.subTest(param=param.name):
                result = self.z.percent(M, 12, 150, parameter=param, value=2.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in ZAPLETAL_1987.Parameters:
            with self.subTest(param=param.name):
                result = self.z.percent(F, 12, 145, parameter=param, value=2.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        r_m = self.z.percent(M, 12, 150, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)
        r_f = self.z.percent(F, 12, 145, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)
        self.assertNotAlmostEqual(r_m, r_f, places=1)

    def test_power10_formula_fvc_scales_with_height(self):
        r_small = self.z.percent(M, 12, 130, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)
        r_tall = self.z.percent(M, 12, 165, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)
        # Taller child → higher predicted FVC → lower percent for same value
        self.assertGreater(r_small, r_tall)

    def test_fev1fvc_linear_formula(self):
        # FEV1FVC uses a linear formula (not power10), result should be a reasonable %
        result = self.z.percent(M, 12, 150, parameter=ZAPLETAL_1987.Parameters.FEV1FVC, value=80.0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)


class TestZapletal1987NoLLN(unittest.TestCase):

    def setUp(self):
        self.z = ZAPLETAL_1987()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.z.lln(M, 12, 150, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.z.uln(M, 12, 150, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.z.zscore(M, 12, 150, parameter=ZAPLETAL_1987.Parameters.FVC, value=2.5)))


class TestZapletal1987OutOfRange(unittest.TestCase):

    def setUp(self):
        self.z = ZAPLETAL_1987()

    def test_age_below_range_returns_na(self):
        result = self.z.percent(M, 5, 120, parameter=ZAPLETAL_1987.Parameters.FVC, value=1.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.z.percent(M, 19, 175, parameter=ZAPLETAL_1987.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_height_below_range_returns_na(self):
        result = self.z.percent(M, 10, 106, parameter=ZAPLETAL_1987.Parameters.FVC, value=1.5)
        self.assertTrue(pd.isna(result))

    def test_height_above_range_returns_na(self):
        result = self.z.percent(M, 16, 183, parameter=ZAPLETAL_1987.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

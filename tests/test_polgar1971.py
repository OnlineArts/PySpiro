import unittest
import pandas as pd
from pyspiro import POLGAR_1971

M = 1
F = 0


class TestPolgar1971Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(POLGAR_1971())

    def test_age_range(self):
        p = POLGAR_1971()
        self.assertEqual(p._age_range, (4, 17))

    def test_height_range(self):
        p = POLGAR_1971()
        self.assertEqual(p._HEIGHT_RANGE, (110.0, 170.0))

    def test_parameters_enum(self):
        params = [p.name for p in POLGAR_1971.Parameters]
        for name in ('FVC', 'FEV1', 'FEF25_75', 'PEFR', 'MVV'):
            self.assertIn(name, params)


class TestPolgar1971Percent(unittest.TestCase):

    def setUp(self):
        self.p = POLGAR_1971()

    def test_known_fvc_male(self):
        result = self.p.percent(M, 12, 140, parameter=POLGAR_1971.Parameters.FVC, value=2.0)
        self.assertAlmostEqual(result, 84.61, places=1)

    def test_all_parameters_return_float_male(self):
        for param in POLGAR_1971.Parameters:
            with self.subTest(param=param.name):
                result = self.p.percent(M, 12, 140, parameter=param, value=2.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in POLGAR_1971.Parameters:
            with self.subTest(param=param.name):
                result = self.p.percent(F, 12, 135, parameter=param, value=2.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        r_m = self.p.percent(M, 12, 140, parameter=POLGAR_1971.Parameters.FVC, value=2.0)
        r_f = self.p.percent(F, 12, 135, parameter=POLGAR_1971.Parameters.FVC, value=2.0)
        self.assertNotAlmostEqual(r_m, r_f, places=1)

    def test_power_type_fvc_scales_with_height(self):
        r_small = self.p.percent(M, 12, 130, parameter=POLGAR_1971.Parameters.FVC, value=2.0)
        r_tall = self.p.percent(M, 12, 155, parameter=POLGAR_1971.Parameters.FVC, value=2.0)
        # Taller child has higher predicted FVC → lower percent for same value
        self.assertGreater(r_small, r_tall)


class TestPolgar1971NoLLN(unittest.TestCase):

    def setUp(self):
        self.p = POLGAR_1971()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.p.lln(M, 12, 140, parameter=POLGAR_1971.Parameters.FVC, value=2.0)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.p.uln(M, 12, 140, parameter=POLGAR_1971.Parameters.FVC, value=2.0)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.p.zscore(M, 12, 140, parameter=POLGAR_1971.Parameters.FVC, value=2.0)))


class TestPolgar1971OutOfRange(unittest.TestCase):

    def setUp(self):
        self.p = POLGAR_1971()

    def test_age_below_range_returns_na(self):
        result = self.p.percent(M, 3, 120, parameter=POLGAR_1971.Parameters.FVC, value=1.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.p.percent(M, 18, 160, parameter=POLGAR_1971.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_height_below_range_returns_na(self):
        result = self.p.percent(M, 10, 109, parameter=POLGAR_1971.Parameters.FVC, value=1.5)
        self.assertTrue(pd.isna(result))

    def test_height_above_range_returns_na(self):
        result = self.p.percent(M, 14, 171, parameter=POLGAR_1971.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

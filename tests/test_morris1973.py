import unittest
import pandas as pd
from pyspiro import MORRIS_1973

M = 1
F = 0


class TestMorris1973Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(MORRIS_1973())

    def test_age_range(self):
        m = MORRIS_1973()
        self.assertEqual(m._age_range, (20, 90))

    def test_height_ranges(self):
        m = MORRIS_1973()
        self.assertEqual(m._HEIGHT_MALE_RANGE, (147.3, 203.2))
        self.assertEqual(m._HEIGHT_FEMALE_RANGE, (142.2, 182.9))

    def test_parameters_enum(self):
        params = [p.name for p in MORRIS_1973.Parameters]
        for name in ('FVC', 'FEV1', 'FEF25_75', 'FEV1FVC'):
            self.assertIn(name, params)


class TestMorris1973Percent(unittest.TestCase):

    def setUp(self):
        self.m = MORRIS_1973()

    def test_known_fvc_male(self):
        result = self.m.percent(M, 40, 175, parameter=MORRIS_1973.Parameters.FVC, value=4.0)
        self.assertAlmostEqual(result, 80.71, places=1)

    def test_all_parameters_return_float_male(self):
        for param in MORRIS_1973.Parameters:
            with self.subTest(param=param.name):
                result = self.m.percent(M, 40, 175, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in [MORRIS_1973.Parameters.FVC, MORRIS_1973.Parameters.FEV1,
                      MORRIS_1973.Parameters.FEF25_75]:
            with self.subTest(param=param.name):
                result = self.m.percent(F, 40, 163, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        r_m = self.m.percent(M, 40, 175, parameter=MORRIS_1973.Parameters.FVC, value=4.0)
        r_f = self.m.percent(F, 40, 163, parameter=MORRIS_1973.Parameters.FVC, value=4.0)
        self.assertNotAlmostEqual(r_m, r_f, places=1)


class TestMorris1973FEV1FVCAgeRange(unittest.TestCase):
    """FEV1FVC has a narrower valid age range (20–79) than other parameters."""

    def setUp(self):
        self.m = MORRIS_1973()

    def test_fev1fvc_valid_at_age_79(self):
        result = self.m.percent(M, 79, 175, parameter=MORRIS_1973.Parameters.FEV1FVC, value=70.0)
        self.assertIsInstance(result, float)

    def test_fev1fvc_returns_na_at_age_80(self):
        result = self.m.percent(M, 80, 175, parameter=MORRIS_1973.Parameters.FEV1FVC, value=70.0)
        self.assertTrue(pd.isna(result))

    def test_fvc_still_valid_at_age_80(self):
        result = self.m.percent(M, 80, 175, parameter=MORRIS_1973.Parameters.FVC, value=3.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)


class TestMorris1973NoLLN(unittest.TestCase):

    def setUp(self):
        self.m = MORRIS_1973()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.m.lln(M, 40, 175, parameter=MORRIS_1973.Parameters.FVC, value=4.0)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.m.uln(M, 40, 175, parameter=MORRIS_1973.Parameters.FVC, value=4.0)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.m.zscore(M, 40, 175, parameter=MORRIS_1973.Parameters.FVC, value=4.0)))


class TestMorris1973OutOfRange(unittest.TestCase):

    def setUp(self):
        self.m = MORRIS_1973()

    def test_age_below_range_returns_na(self):
        result = self.m.percent(M, 19, 175, parameter=MORRIS_1973.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.m.percent(M, 91, 175, parameter=MORRIS_1973.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))

    def test_male_height_below_range_returns_na(self):
        result = self.m.percent(M, 40, 147, parameter=MORRIS_1973.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_female_height_above_range_returns_na(self):
        result = self.m.percent(F, 40, 183, parameter=MORRIS_1973.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

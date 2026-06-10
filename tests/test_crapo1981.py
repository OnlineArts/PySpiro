import unittest
import pandas as pd
from pyspiro import CRAPO_1981

M = 1
F = 0


class TestCrapo1981Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(CRAPO_1981())

    def test_age_ranges(self):
        c = CRAPO_1981()
        self.assertEqual(c._AGE_MALE_RANGE, (15, 91))
        self.assertEqual(c._AGE_FEMALE_RANGE, (17, 84))

    def test_height_ranges(self):
        c = CRAPO_1981()
        self.assertEqual(c._HEIGHT_MALE_RANGE, (157.0, 194.0))
        self.assertEqual(c._HEIGHT_FEMALE_RANGE, (146.0, 178.0))

    def test_parameters_enum(self):
        params = [p.name for p in CRAPO_1981.Parameters]
        for name in ('FVC', 'FEV05', 'FEV1', 'FEV3', 'FEF25_75', 'FEV1FVC', 'FEV3FVC'):
            self.assertIn(name, params)


class TestCrapo1981Percent(unittest.TestCase):

    def setUp(self):
        self.c = CRAPO_1981()

    def test_known_fvc_male(self):
        result = self.c.percent(M, 40, 175, parameter=CRAPO_1981.Parameters.FVC, value=4.0)
        self.assertAlmostEqual(result, 80.1, places=1)

    def test_known_fev1_female(self):
        result = self.c.percent(F, 40, 163, parameter=CRAPO_1981.Parameters.FEV1, value=2.8)
        self.assertAlmostEqual(result, 94.07, places=1)

    def test_all_parameters_return_float_male(self):
        for param in CRAPO_1981.Parameters:
            with self.subTest(param=param.name):
                result = self.c.percent(M, 40, 175, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in CRAPO_1981.Parameters:
            with self.subTest(param=param.name):
                result = self.c.percent(F, 40, 163, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        m = self.c.percent(M, 40, 175, parameter=CRAPO_1981.Parameters.FVC, value=4.0)
        f = self.c.percent(F, 40, 163, parameter=CRAPO_1981.Parameters.FVC, value=4.0)
        self.assertNotAlmostEqual(m, f, places=1)


class TestCrapo1981NoLLN(unittest.TestCase):

    def setUp(self):
        self.c = CRAPO_1981()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.c.lln(M, 40, 175, parameter=CRAPO_1981.Parameters.FVC, value=4.0)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.c.uln(M, 40, 175, parameter=CRAPO_1981.Parameters.FVC, value=4.0)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.c.zscore(M, 40, 175, parameter=CRAPO_1981.Parameters.FVC, value=4.0)))


class TestCrapo1981OutOfRange(unittest.TestCase):

    def setUp(self):
        self.c = CRAPO_1981()

    def test_male_age_below_range_returns_na(self):
        result = self.c.percent(M, 14, 175, parameter=CRAPO_1981.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_male_age_above_range_returns_na(self):
        result = self.c.percent(M, 92, 175, parameter=CRAPO_1981.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_female_age_below_range_returns_na(self):
        result = self.c.percent(F, 16, 163, parameter=CRAPO_1981.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))

    def test_female_age_above_range_returns_na(self):
        result = self.c.percent(F, 85, 163, parameter=CRAPO_1981.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))

    def test_male_height_below_range_returns_na(self):
        result = self.c.percent(M, 40, 156, parameter=CRAPO_1981.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_female_height_above_range_returns_na(self):
        result = self.c.percent(F, 40, 179, parameter=CRAPO_1981.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

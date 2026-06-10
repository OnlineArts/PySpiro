import unittest
import pandas as pd
from pyspiro import CHERNIACK_1972

M = 1
F = 0


class TestCherniack1972Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(CHERNIACK_1972())

    def test_age_range(self):
        c = CHERNIACK_1972()
        self.assertEqual(c._age_range, (15, 79))

    def test_height_range(self):
        c = CHERNIACK_1972()
        self.assertEqual(c._HEIGHT_RANGE, (88.9, 215.9))

    def test_parameters_enum(self):
        params = [p.name for p in CHERNIACK_1972.Parameters]
        for name in ('FVC', 'FEV1', 'FEF25', 'FEF50', 'FEF75', 'FEF25_75', 'PEFR', 'MVV'):
            self.assertIn(name, params)


class TestCherniack1972Percent(unittest.TestCase):

    def setUp(self):
        self.c = CHERNIACK_1972()

    def test_known_fvc_male(self):
        result = self.c.percent(M, 40, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertAlmostEqual(result, 75.9, places=1)

    def test_known_fev1_female(self):
        result = self.c.percent(F, 40, 163, parameter=CHERNIACK_1972.Parameters.FEV1, value=2.8)
        self.assertAlmostEqual(result, 96.3, places=1)

    def test_all_parameters_return_float_male(self):
        for param in CHERNIACK_1972.Parameters:
            with self.subTest(param=param.name):
                result = self.c.percent(M, 40, 175, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in CHERNIACK_1972.Parameters:
            with self.subTest(param=param.name):
                result = self.c.percent(F, 40, 163, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        m = self.c.percent(M, 40, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        f = self.c.percent(F, 40, 163, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertNotAlmostEqual(m, f, places=1)


class TestCherniack1972NoLLN(unittest.TestCase):

    def setUp(self):
        self.c = CHERNIACK_1972()

    def test_lln_returns_na(self):
        result = self.c.lln(M, 40, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_uln_returns_na(self):
        result = self.c.uln(M, 40, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_zscore_returns_na(self):
        result = self.c.zscore(M, 40, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_lms_returns_na_triple(self):
        l, m, s = self.c.lms(M, 40, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(l))
        self.assertTrue(pd.isna(m))
        self.assertTrue(pd.isna(s))


class TestCherniack1972OutOfRange(unittest.TestCase):

    def setUp(self):
        self.c = CHERNIACK_1972()

    def test_age_below_range_returns_na(self):
        result = self.c.percent(M, 14, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.c.percent(M, 80, 175, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_height_below_range_returns_na(self):
        result = self.c.percent(M, 40, 88, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_height_above_range_returns_na(self):
        result = self.c.percent(M, 40, 216, parameter=CHERNIACK_1972.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

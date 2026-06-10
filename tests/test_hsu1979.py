import unittest
import pandas as pd
from pyspiro import HSU_1979

M = 1
F = 0
CAUCASIAN = HSU_1979.Ethnicity.CAUCASIAN.value
AFRICAN_AMERICAN = HSU_1979.Ethnicity.AFRICAN_AMERICAN.value
MEXICAN = HSU_1979.Ethnicity.MEXICAN_AMERICAN.value


class TestHsu1979Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(HSU_1979())

    def test_age_ranges(self):
        h = HSU_1979()
        self.assertEqual(h._AGE_MALE_RANGE, (7, 20))
        self.assertEqual(h._AGE_FEMALE_RANGE, (7, 18))

    def test_height_range(self):
        h = HSU_1979()
        self.assertEqual(h._HEIGHT_RANGE, (111.0, 190.0))

    def test_parameters_enum(self):
        params = [p.name for p in HSU_1979.Parameters]
        for name in ('FVC', 'FEV1', 'PEFR', 'FEF25_75'):
            self.assertIn(name, params)

    def test_ethnicity_enum(self):
        eths = [e.name for e in HSU_1979.Ethnicity]
        for name in ('CAUCASIAN', 'AFRICAN_AMERICAN', 'MEXICAN_AMERICAN'):
            self.assertIn(name, eths)


class TestHsu1979Percent(unittest.TestCase):

    def setUp(self):
        self.h = HSU_1979()

    def test_known_fvc_male_caucasian(self):
        result = self.h.percent(M, 15, 155, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.0)
        self.assertAlmostEqual(result, 90.78, places=1)

    def test_all_parameters_return_float_male_caucasian(self):
        for param in HSU_1979.Parameters:
            with self.subTest(param=param.name):
                result = self.h.percent(M, 15, 155, CAUCASIAN, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_ethnicities_return_float(self):
        for eth in (CAUCASIAN, AFRICAN_AMERICAN, MEXICAN):
            with self.subTest(ethnicity=eth):
                result = self.h.percent(M, 15, 155, eth, parameter=HSU_1979.Parameters.FVC, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_ethnicities_differ(self):
        r_caucasian = self.h.percent(M, 15, 155, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.0)
        r_african_american = self.h.percent(M, 15, 155, AFRICAN_AMERICAN, parameter=HSU_1979.Parameters.FVC, value=3.0)
        self.assertNotAlmostEqual(r_caucasian, r_african_american, places=1)

    def test_male_and_female_differ(self):
        r_m = self.h.percent(M, 15, 155, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.0)
        r_f = self.h.percent(F, 15, 155, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.0)
        self.assertNotAlmostEqual(r_m, r_f, places=1)


class TestHsu1979NoLLN(unittest.TestCase):

    def setUp(self):
        self.h = HSU_1979()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.h.lln(M, 15, 155, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.0)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.h.uln(M, 15, 155, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.0)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.h.zscore(M, 15, 155, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.0)))


class TestHsu1979OutOfRange(unittest.TestCase):

    def setUp(self):
        self.h = HSU_1979()

    def test_age_below_range_returns_na(self):
        result = self.h.percent(M, 6, 120, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=1.5)
        self.assertTrue(pd.isna(result))

    def test_male_age_above_range_returns_na(self):
        result = self.h.percent(M, 21, 170, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_female_age_above_range_returns_na(self):
        result = self.h.percent(F, 19, 165, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_height_below_range_returns_na(self):
        result = self.h.percent(M, 10, 110, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=1.0)
        self.assertTrue(pd.isna(result))

    def test_height_above_range_returns_na(self):
        result = self.h.percent(M, 18, 191, CAUCASIAN, parameter=HSU_1979.Parameters.FVC, value=5.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

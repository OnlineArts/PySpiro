import unittest
import pandas as pd
from pyspiro import ECCS_1993

M = 1
F = 0


class TestEccs1993Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(ECCS_1993())

    def test_age_range(self):
        e = ECCS_1993()
        self.assertEqual(e._AGE_RANGE, (18, 70))

    def test_height_ranges(self):
        e = ECCS_1993()
        self.assertEqual(e._HEIGHT_MALE_RANGE, (155.0, 195.0))
        self.assertEqual(e._HEIGHT_FEMALE_RANGE, (145.0, 180.0))

    def test_parameters_enum(self):
        params = [p.name for p in ECCS_1993.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'FEF25', 'FEF50', 'FEF75', 'FEF25_75', 'PEFR', 'FIVC'):
            self.assertIn(name, params)


class TestEccs1993Percent(unittest.TestCase):

    def setUp(self):
        self.e = ECCS_1993()

    def test_known_fvc_male(self):
        result = self.e.percent(M, 40, 175, parameter=ECCS_1993.Parameters.FVC, value=4.0)
        self.assertAlmostEqual(result, 85.11, places=1)

    def test_all_parameters_return_float_male(self):
        for param in ECCS_1993.Parameters:
            with self.subTest(param=param.name):
                result = self.e.percent(M, 40, 175, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in ECCS_1993.Parameters:
            with self.subTest(param=param.name):
                result = self.e.percent(F, 40, 163, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        m = self.e.percent(M, 40, 175, parameter=ECCS_1993.Parameters.FVC, value=4.0)
        f = self.e.percent(F, 40, 163, parameter=ECCS_1993.Parameters.FVC, value=4.0)
        self.assertNotAlmostEqual(m, f, places=1)

    def test_male_fef75_age_clamped_below_25(self):
        # FEF75 male: age clamped to 25 for subjects 18–25
        result_20 = self.e.percent(M, 20, 170, parameter=ECCS_1993.Parameters.FEF75, value=3.0)
        result_25 = self.e.percent(M, 25, 170, parameter=ECCS_1993.Parameters.FEF75, value=3.0)
        self.assertAlmostEqual(result_20, result_25, places=5)

    def test_male_fivc_age_clamped_below_25(self):
        # FIVC male: age clamped to 25 for subjects 18–25
        result_18 = self.e.percent(M, 18, 170, parameter=ECCS_1993.Parameters.FIVC, value=3.0)
        result_25 = self.e.percent(M, 25, 170, parameter=ECCS_1993.Parameters.FIVC, value=3.0)
        self.assertAlmostEqual(result_18, result_25, places=5)

    def test_male_fef25_not_clamped(self):
        # FEF25 male is NOT clamped: age 20 and 25 give different results
        result_20 = self.e.percent(M, 20, 170, parameter=ECCS_1993.Parameters.FEF25, value=5.0)
        result_25 = self.e.percent(M, 25, 170, parameter=ECCS_1993.Parameters.FEF25, value=5.0)
        self.assertNotAlmostEqual(result_20, result_25, places=5)

    def test_female_fvc_age_clamped_below_25(self):
        # All female params are clamped: FVC at age 20 == FVC at age 25
        result_20 = self.e.percent(F, 20, 163, parameter=ECCS_1993.Parameters.FVC, value=3.0)
        result_25 = self.e.percent(F, 25, 163, parameter=ECCS_1993.Parameters.FVC, value=3.0)
        self.assertAlmostEqual(result_20, result_25, places=5)

    def test_female_fef25_age_clamped_below_25(self):
        result_18 = self.e.percent(F, 18, 163, parameter=ECCS_1993.Parameters.FEF25, value=3.0)
        result_25 = self.e.percent(F, 25, 163, parameter=ECCS_1993.Parameters.FEF25, value=3.0)
        self.assertAlmostEqual(result_18, result_25, places=5)

    def test_clamping_does_not_apply_above_25(self):
        # Above age 25 the formula runs normally for both sexes
        result_25 = self.e.percent(M, 25, 170, parameter=ECCS_1993.Parameters.FEF75, value=3.0)
        result_40 = self.e.percent(M, 40, 170, parameter=ECCS_1993.Parameters.FEF75, value=3.0)
        self.assertNotAlmostEqual(result_25, result_40, places=5)


class TestEccs1993NoLLN(unittest.TestCase):

    def setUp(self):
        self.e = ECCS_1993()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.e.lln(M, 40, 175, parameter=ECCS_1993.Parameters.FVC, value=4.0)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.e.uln(M, 40, 175, parameter=ECCS_1993.Parameters.FVC, value=4.0)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.e.zscore(M, 40, 175, parameter=ECCS_1993.Parameters.FVC, value=4.0)))


class TestEccs1993OutOfRange(unittest.TestCase):

    def setUp(self):
        self.e = ECCS_1993()

    def test_age_below_range_returns_na(self):
        result = self.e.percent(M, 17, 175, parameter=ECCS_1993.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.e.percent(M, 71, 175, parameter=ECCS_1993.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_male_height_below_range_returns_na(self):
        result = self.e.percent(M, 40, 154, parameter=ECCS_1993.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_female_height_above_range_returns_na(self):
        result = self.e.percent(F, 40, 181, parameter=ECCS_1993.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

import unittest
import pandas as pd
from pyspiro import GLI_2012


M = 1  # male
F = 0  # female
E_W = GLI_2012.Ethnicity.CAUCASIAN.value
E_B = GLI_2012.Ethnicity.AFRICAN_AMERICAN.value
E_NE = GLI_2012.Ethnicity.NORTHEAST_ASIAN.value
E_SE = GLI_2012.Ethnicity.SOUTHEAST_ASIAN.value


class TestGLI2012Instantiation(unittest.TestCase):

    def test_instantiation(self):
        gli = GLI_2012()
        self.assertIsNotNone(gli)

    def test_age_range_set(self):
        gli = GLI_2012()
        self.assertEqual(gli._age_range[0], 3)
        self.assertEqual(gli._age_range[1], 95)


class TestGLI2012Percent(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()

    def test_percent_known_fev1_male(self):
        # Male, 40y, 175 cm, Caucasian, FEV1=3.0 L
        result = self.gli.percent(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertAlmostEqual(result, 73.57, places=1)

    def test_percent_returns_float(self):
        result = self.gli.percent(F, 35, 165, E_W, GLI_2012.Parameters.FVC, 3.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_percent_at_median_is_100(self):
        l, m, s = self.gli.lms(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        result = self.gli.percent(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, m)
        self.assertAlmostEqual(result, 100.0, places=1)

    def test_percent_female_differs_from_male(self):
        p_m = self.gli.percent(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        p_f = self.gli.percent(F, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertNotAlmostEqual(p_m, p_f, places=1)

    def test_percent_ethnicity_affects_result(self):
        p_cau = self.gli.percent(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        p_afr = self.gli.percent(M, 40, 175, E_B, GLI_2012.Parameters.FEV1, 3.0)
        self.assertNotAlmostEqual(p_cau, p_afr, places=1)

    def test_core_parameters_return_float(self):
        # FEV075 and FEV075FVC are in the Parameters enum but their splines are
        # absent from the current gli_2012_splines.csv; test only present ones.
        core = [GLI_2012.Parameters.FEV1, GLI_2012.Parameters.FVC,
                GLI_2012.Parameters.FEV1FVC, GLI_2012.Parameters.FEF25_75,
                GLI_2012.Parameters.FEF75]
        for param in core:
            with self.subTest(param=param.name):
                result = self.gli.percent(M, 40, 175, E_W, param, 3.0)
                self.assertFalse(pd.isna(result))


class TestGLI2012ZScore(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()

    def test_zscore_at_median_is_zero(self):
        l, m, s = self.gli.lms(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        result = self.gli.zscore(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, m)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_zscore_below_median_is_negative(self):
        l, m, s = self.gli.lms(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        result = self.gli.zscore(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, m * 0.8)
        self.assertLess(result, 0)

    def test_zscore_above_median_is_positive(self):
        l, m, s = self.gli.lms(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        result = self.gli.zscore(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, m * 1.2)
        self.assertGreater(result, 0)


class TestGLI2012LimitsOfNormal(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()

    def test_lln_less_than_predicted_median(self):
        l, m, s = self.gli.lms(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        lln = self.gli.lln(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, m)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted_median(self):
        l, m, s = self.gli.lms(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        uln = self.gli.uln(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, m)
        self.assertGreater(uln, m)

    def test_lln_corresponds_to_lln_zscore(self):
        # The value at LLN should give z ≈ -1.645
        lln = self.gli.lln(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        z = self.gli.zscore(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, lln)
        self.assertAlmostEqual(z, -1.645, places=2)

    def test_uln_corresponds_to_uln_zscore(self):
        uln = self.gli.uln(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        z = self.gli.zscore(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, uln)
        self.assertAlmostEqual(z, 1.645, places=2)


class TestGLI2012OutOfRange(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()

    def test_age_below_range_returns_na(self):
        result = self.gli.percent(M, 2, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.gli.percent(M, 96, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertTrue(pd.isna(result))


class TestGLI2012All(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()

    def test_all_returns_three_tuple(self):
        result = self.gli.all(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_all_values_are_finite(self):
        pct, z, lln = self.gli.all(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertFalse(pd.isna(pct))
        self.assertFalse(pd.isna(z))
        self.assertFalse(pd.isna(lln))


if __name__ == "__main__":
    unittest.main()

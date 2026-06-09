import unittest
import pandas as pd
from pyspiro import GLI_2017


M = 1
F = 0


class TestGLI2017Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(GLI_2017())

    def test_age_range(self):
        gli = GLI_2017()
        self.assertEqual(gli._age_range[0], 5)
        self.assertGreaterEqual(gli._age_range[1], 80)  # splines extend to 90


class TestGLI2017Percent(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2017()

    def test_percent_known_kco_si_male(self):
        # Male, 40y, 175 cm, KCO_SI=1.5 → 94.62%
        result = self.gli.percent(M, 40, 175, GLI_2017.Parameters.KCO_SI, 1.5)
        self.assertAlmostEqual(result, 94.62, places=1)

    def test_percent_at_median_is_100(self):
        l, m, s = self.gli.lms(M, 40, 175, GLI_2017.Parameters.KCO_SI, 0)
        result = self.gli.percent(M, 40, 175, GLI_2017.Parameters.KCO_SI, m)
        self.assertAlmostEqual(result, 100.0, places=1)

    def test_all_parameters_return_float(self):
        for param in GLI_2017.Parameters:
            with self.subTest(param=param.name):
                result = self.gli.percent(M, 40, 175, param, 1.5)
                self.assertFalse(pd.isna(result))

    def test_female_differs_from_male(self):
        p_m = self.gli.percent(M, 40, 175, GLI_2017.Parameters.KCO_SI, 1.5)
        p_f = self.gli.percent(F, 40, 175, GLI_2017.Parameters.KCO_SI, 1.5)
        self.assertNotAlmostEqual(p_m, p_f, places=1)


class TestGLI2017LimitsOfNormal(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2017()

    def test_lln_less_than_predicted(self):
        l, m, s = self.gli.lms(M, 40, 175, GLI_2017.Parameters.KCO_SI, 0)
        lln = self.gli.lln(M, 40, 175, GLI_2017.Parameters.KCO_SI, m)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted(self):
        l, m, s = self.gli.lms(M, 40, 175, GLI_2017.Parameters.KCO_SI, 0)
        uln = self.gli.uln(M, 40, 175, GLI_2017.Parameters.KCO_SI, m)
        self.assertGreater(uln, m)

    def test_lln_zscore_is_minus_1645(self):
        lln = self.gli.lln(M, 40, 175, GLI_2017.Parameters.KCO_SI, 0)
        z = self.gli.zscore(M, 40, 175, GLI_2017.Parameters.KCO_SI, lln)
        self.assertAlmostEqual(z, -1.645, places=2)


class TestGLI2017OutOfRange(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2017()

    def test_age_below_range_returns_na(self):
        result = self.gli.percent(M, 4, 175, GLI_2017.Parameters.TLCO, 7.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        gli = GLI_2017()
        above = gli._age_range[1] + 1
        result = gli.percent(M, above, 175, GLI_2017.Parameters.TLCO, 7.0)
        self.assertTrue(pd.isna(result))


if __name__ == "__main__":
    unittest.main()

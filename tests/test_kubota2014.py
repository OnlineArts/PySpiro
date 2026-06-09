import unittest
import pandas as pd
from pyspiro import KUBOTA_2014


M = 1
F = 0


class TestKubota2014Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(KUBOTA_2014())

    def test_age_range(self):
        k = KUBOTA_2014()
        self.assertEqual(k._AGE_RANGE, (17, 95))

    def test_parameters_enum(self):
        names = [p.name for p in KUBOTA_2014.Parameters]
        self.assertIn("FEV1", names)
        self.assertIn("FVC", names)
        self.assertIn("VC", names)
        self.assertIn("FEV1FVC", names)


class TestKubota2014Percent(unittest.TestCase):

    def setUp(self):
        self.k = KUBOTA_2014()

    def test_percent_known_fev1_male(self):
        # Male, 40y, 170 cm, FEV1=3.0 L → 84.33%
        result = self.k.percent(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertAlmostEqual(result, 84.33, places=1)

    def test_percent_known_fvc_female(self):
        # Female, 55y, 155 cm, FVC=2.5 L → 89.99%
        result = self.k.percent(F, 55, 155, KUBOTA_2014.Parameters.FVC, 2.5)
        self.assertAlmostEqual(result, 89.99, places=1)

    def test_percent_at_median_is_100(self):
        l, m, s = self.k.lms(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 0)
        result = self.k.percent(M, 40, 170, KUBOTA_2014.Parameters.FEV1, m)
        self.assertAlmostEqual(result, 100.0, places=1)

    def test_fev1fvc_input_is_ratio(self):
        # FEV1FVC M is stored as a ratio (~0.8); pass as ratio (0.75), not %
        result = self.k.percent(M, 50, 170, KUBOTA_2014.Parameters.FEV1FVC, 0.75)
        self.assertAlmostEqual(result, 93.12, places=1)

    def test_all_parameters_return_float(self):
        for param in KUBOTA_2014.Parameters:
            with self.subTest(param=param.name):
                val = 0.75 if param == KUBOTA_2014.Parameters.FEV1FVC else 3.0
                result = self.k.percent(M, 40, 170, param, val)
                self.assertFalse(pd.isna(result))

    def test_female_differs_from_male(self):
        p_m = self.k.percent(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        p_f = self.k.percent(F, 40, 155, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertNotAlmostEqual(p_m, p_f, places=1)


class TestKubota2014ZScore(unittest.TestCase):

    def setUp(self):
        self.k = KUBOTA_2014()

    def test_zscore_at_median_is_zero(self):
        l, m, s = self.k.lms(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 0)
        result = self.k.zscore(M, 40, 170, KUBOTA_2014.Parameters.FEV1, m)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_zscore_below_median_is_negative(self):
        result = self.k.zscore(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertLess(result, 0)


class TestKubota2014LimitsOfNormal(unittest.TestCase):

    def setUp(self):
        self.k = KUBOTA_2014()

    def test_lln_known_value(self):
        # Male, 40y, 170 cm, FEV1 → LLN ≈ 2.9223
        result = self.k.lln(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertAlmostEqual(result, 2.9223, places=2)

    def test_uln_known_value(self):
        # Female, 55y, 155 cm, FVC → ULN ≈ 3.3409
        result = self.k.uln(F, 55, 155, KUBOTA_2014.Parameters.FVC, 2.5)
        self.assertAlmostEqual(result, 3.3409, places=2)

    def test_lln_less_than_predicted(self):
        l, m, s = self.k.lms(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 0)
        lln = self.k.lln(M, 40, 170, KUBOTA_2014.Parameters.FEV1, m)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted(self):
        l, m, s = self.k.lms(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 0)
        uln = self.k.uln(M, 40, 170, KUBOTA_2014.Parameters.FEV1, m)
        self.assertGreater(uln, m)

    def test_lln_zscore_is_minus_1645(self):
        lln = self.k.lln(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 0)
        z = self.k.zscore(M, 40, 170, KUBOTA_2014.Parameters.FEV1, lln)
        self.assertAlmostEqual(z, -1.645, places=2)

    def test_uln_zscore_is_plus_1645(self):
        uln = self.k.uln(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 0)
        z = self.k.zscore(M, 40, 170, KUBOTA_2014.Parameters.FEV1, uln)
        self.assertAlmostEqual(z, 1.645, places=2)


class TestKubota2014FEV1FVCLspline(unittest.TestCase):
    """FEV1FVC is the only parameter with a non-zero Lspline (age-varying L)."""

    def setUp(self):
        self.k = KUBOTA_2014()

    def test_l_is_age_dependent_for_fev1fvc(self):
        l_40, _, _ = self.k.lms(M, 40, 170, KUBOTA_2014.Parameters.FEV1FVC, 0)
        l_70, _, _ = self.k.lms(M, 70, 170, KUBOTA_2014.Parameters.FEV1FVC, 0)
        self.assertNotAlmostEqual(l_40, l_70, places=3)

    def test_l_is_constant_for_fev1(self):
        l_40, _, _ = self.k.lms(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 0)
        l_70, _, _ = self.k.lms(M, 70, 170, KUBOTA_2014.Parameters.FEV1, 0)
        self.assertAlmostEqual(l_40, l_70, places=5)


class TestKubota2014OutOfRange(unittest.TestCase):

    def setUp(self):
        self.k = KUBOTA_2014()

    def test_age_below_range_returns_na(self):
        result = self.k.percent(M, 16, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.k.percent(M, 96, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertTrue(pd.isna(result))

    def test_female_na_at_age_94(self):
        # Female FEV1 spline is NA at ages 94-95
        result = self.k.percent(F, 94, 155, KUBOTA_2014.Parameters.FEV1, 2.0)
        self.assertTrue(pd.isna(result))


class TestKubota2014AgeFlooring(unittest.TestCase):

    def setUp(self):
        self.k = KUBOTA_2014()

    def test_fractional_age_uses_integer_splines(self):
        # __get_splines returns (Sspline, Mspline, Lspline)
        # Both int(40.0)=40 and int(40.7)=40 produce identical Sspline values
        sspline1, _, _ = self.k._KUBOTA_2014__get_splines(M, 40, KUBOTA_2014.Parameters.FEV1.value)
        sspline2, _, _ = self.k._KUBOTA_2014__get_splines(M, 40, KUBOTA_2014.Parameters.FEV1.value)
        self.assertAlmostEqual(sspline1, sspline2, places=10)


class TestKubota2014All(unittest.TestCase):

    def setUp(self):
        self.k = KUBOTA_2014()

    def test_all_returns_four_tuple(self):
        result = self.k.all(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)

    def test_all_values_consistent_with_individual_methods(self):
        pct, z, lln, uln = self.k.all(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0)
        self.assertAlmostEqual(pct,
            self.k.percent(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0), places=4)
        self.assertAlmostEqual(z,
            self.k.zscore(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0), places=4)
        self.assertAlmostEqual(lln,
            self.k.lln(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0), places=4)
        self.assertAlmostEqual(uln,
            self.k.uln(M, 40, 170, KUBOTA_2014.Parameters.FEV1, 3.0), places=4)


if __name__ == "__main__":
    unittest.main()

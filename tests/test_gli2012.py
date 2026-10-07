import math
import unittest
import pandas as pd
from pyspiro import GLI_2012


M = 1  # male
F = 0  # female
E_W = GLI_2012.Ethnicity.CAUCASIAN.value
E_B = GLI_2012.Ethnicity.AFRICAN_AMERICAN.value
E_NE = GLI_2012.Ethnicity.NORTHEAST_ASIAN.value
E_SE = GLI_2012.Ethnicity.SOUTHEAST_ASIAN.value
E_O = GLI_2012.Ethnicity.OTHER.value


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
        core = [GLI_2012.Parameters.FEV1, GLI_2012.Parameters.FVC,
                GLI_2012.Parameters.FEV1FVC, GLI_2012.Parameters.FEF25_75,
                GLI_2012.Parameters.FEF75]
        for param in core:
            with self.subTest(param=param.name):
                result = self.gli.percent(M, 40, 175, E_W, param, 3.0)
                self.assertFalse(pd.isna(result))

    def test_every_parameter_is_computable(self):
        # FEV0.75 and FEV0.75/FVC are defined for Caucasians aged 3-7 y only
        for param in GLI_2012.Parameters:
            for sex in (M, F):
                with self.subTest(param=param.name, sex=sex):
                    result = self.gli.percent(sex, 5, 110, E_W, param, 1.0)
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

    def test_all_returns_four_tuple(self):
        result = self.gli.all(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)

    def test_all_values_are_finite(self):
        pct, z, lln, uln = self.gli.all(M, 40, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)
        self.assertFalse(pd.isna(pct))
        self.assertFalse(pd.isna(z))
        self.assertFalse(pd.isna(lln))
        self.assertFalse(pd.isna(uln))


class TestGLI2012WorkedExamples(unittest.TestCase):
    """Worked examples 4.3.1 and 4.3.2 of the GLI-2012 online supplement (Quanjer 2012)."""

    def setUp(self):
        self.gli = GLI_2012()
        self.fev1 = GLI_2012.Parameters.FEV1

    def test_white_boy_4_3_1(self):
        # 4.8 y, 107 cm, FEV1 = 0.800 L
        l, m, s = self.gli.lms(M, 4.8, 107, E_W, self.fev1, 0.800)
        self.assertAlmostEqual(m, 1.0442, places=4)
        self.assertAlmostEqual(s, 0.1296, places=4)
        self.assertAlmostEqual(l, 1.0199, places=4)
        self.assertAlmostEqual(self.gli.percent(M, 4.8, 107, E_W, self.fev1, 0.800), 76.6, places=1)
        self.assertAlmostEqual(self.gli.zscore(M, 4.8, 107, E_W, self.fev1, 0.800), -1.80, places=2)

    def test_african_american_boy_4_3_2(self):
        # 12.2 y, 152 cm, FEV1 = 2.405 L
        l, m, s = self.gli.lms(M, 12.2, 152, E_B, self.fev1, 2.405)
        self.assertAlmostEqual(m, 2.1860, places=4)
        self.assertAlmostEqual(s, 0.1284, places=4)
        self.assertAlmostEqual(l, 1.0992, places=4)
        self.assertAlmostEqual(self.gli.percent(M, 12.2, 152, E_B, self.fev1, 2.405), 110.0, places=1)
        self.assertAlmostEqual(self.gli.zscore(M, 12.2, 152, E_B, self.fev1, 2.405), 0.78, places=2)


class TestGLI2012Interpolation(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()

    def test_splines_interpolated_between_quarter_years(self):
        for param in [GLI_2012.Parameters.FEV1, GLI_2012.Parameters.FEV1FVC, GLI_2012.Parameters.FEF75]:
            with self.subTest(param=param.name):
                lo = list(self.gli._get_splines(F, 12.0, param))
                hi = list(self.gli._get_splines(F, 12.25, param))
                mid = self.gli._interpolated_splines(F, 12.1, param, (3, 90))
                for a, b, x in zip(lo, hi, mid):
                    self.assertAlmostEqual(x, 0.6 * a + 0.4 * b, places=12)

    def test_closed_form_terms_use_exact_age(self):
        # Ages 40.1 and 40.0 must differ (no snapping to the quarter-year grid)
        _, m1, _ = self.gli.lms(M, 40.0, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        _, m2, _ = self.gli.lms(M, 40.1, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        self.assertNotAlmostEqual(m1, m2, places=6)

    def test_quarter_year_ages_use_table_row(self):
        c = self.gli._coefficients["FEV1_males"]
        sspline, mspline, _ = self.gli._get_splines(M, 40.25, GLI_2012.Parameters.FEV1)
        _, m, _ = self.gli.lms(M, 40.25, 175, E_W, GLI_2012.Parameters.FEV1, 0)
        expected = math.exp(c.loc["a0"] + c.loc["a1"] * math.log(175) + c.loc["a2"] * math.log(40.25) + mspline)
        self.assertAlmostEqual(m, expected, places=12)

    def test_upper_age_limit_95(self):
        self.assertFalse(pd.isna(self.gli.percent(M, 95, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)))

    def test_ages_between_rows_outside_range_return_na(self):
        self.assertTrue(pd.isna(self.gli.percent(M, 2.9, 100, E_W, GLI_2012.Parameters.FEV1, 1.0)))
        self.assertTrue(pd.isna(self.gli.percent(M, 95.1, 175, E_W, GLI_2012.Parameters.FEV1, 3.0)))

    def test_fef_tables_end_at_90(self):
        for param in [GLI_2012.Parameters.FEF25_75, GLI_2012.Parameters.FEF75]:
            with self.subTest(param=param.name):
                self.assertFalse(pd.isna(self.gli.percent(M, 89.9, 175, E_W, param, 1.0)))
                self.assertTrue(pd.isna(self.gli.percent(M, 90.1, 175, E_W, param, 1.0)))


class TestGLI2012Ethnicity(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()

    def test_other_applies_a6_and_p5(self):
        for param in [GLI_2012.Parameters.FEV1, GLI_2012.Parameters.FVC, GLI_2012.Parameters.FEV1FVC,
                      GLI_2012.Parameters.FEF25_75, GLI_2012.Parameters.FEF75]:
            for sex in (M, F):
                with self.subTest(param=param.name, sex=sex):
                    c = self.gli._coefficients["%s_%ss" % (param.name, GLI_2012.Sex(sex).name.lower())]
                    l_w, m_w, s_w = self.gli.lms(sex, 40, 170, E_W, param, 0)
                    l_o, m_o, s_o = self.gli.lms(sex, 40, 170, E_O, param, 0)
                    self.assertAlmostEqual(l_o, l_w, places=12)
                    self.assertAlmostEqual(m_o, m_w * math.exp(c.loc["a6"]), places=12)
                    self.assertAlmostEqual(s_o, s_w * math.exp(c.loc["p5"]), places=12)

    def test_unknown_ethnicity_raises(self):
        for code in (0, 6, None):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    self.gli.lms(M, 40, 175, code, GLI_2012.Parameters.FEV1, 3.0)


class TestGLI2012FEV075(unittest.TestCase):
    """FEV0.75 and FEV0.75/FVC: equations without look-up tables (GLI-2012 look-up workbook)."""

    def setUp(self):
        self.gli = GLI_2012()

    def test_fev075_male(self):
        l, m, s = self.gli.lms(M, 5, 110, E_W, GLI_2012.Parameters.FEV075, 1.0)
        self.assertEqual(l, 1)
        self.assertAlmostEqual(m, math.exp(-9.28474 + 1.95265 * math.log(110) + 0.02947 * 5), places=12)
        self.assertAlmostEqual(s, math.exp(-1.7947 - 0.06655 * 5), places=12)

    def test_fev075_female(self):
        l, m, s = self.gli.lms(F, 5, 110, E_W, GLI_2012.Parameters.FEV075, 1.0)
        self.assertEqual(l, 1)
        self.assertAlmostEqual(m, math.exp(-10.02391 + 2.11226 * math.log(110) + 0.01937 * 5), places=12)
        self.assertAlmostEqual(s, math.exp(-1.62649 - 0.08282 * 5), places=12)

    def test_fev075fvc_male(self):
        l, m, s = self.gli.lms(M, 5, 110, E_W, GLI_2012.Parameters.FEV075FVC, 0.9)
        self.assertAlmostEqual(l, 2.797, places=12)
        self.assertAlmostEqual(m, math.exp(0.51742 - 0.09404 * math.log(110) - 0.13239 * math.log(5)), places=12)
        self.assertAlmostEqual(s, math.exp(-2.457), places=12)

    def test_fev075fvc_female(self):
        l, m, s = self.gli.lms(F, 5, 110, E_W, GLI_2012.Parameters.FEV075FVC, 0.9)
        self.assertAlmostEqual(l, 3.564, places=12)
        self.assertAlmostEqual(m, math.exp(0.45992 - 0.08914 * math.log(110) - 0.09999 * math.log(5)), places=12)
        self.assertAlmostEqual(s, math.exp(-2.545), places=12)

    def test_outside_3_to_7_years_returns_na(self):
        for param in [GLI_2012.Parameters.FEV075, GLI_2012.Parameters.FEV075FVC]:
            with self.subTest(param=param.name):
                self.assertTrue(pd.isna(self.gli.percent(M, 7.5, 125, E_W, param, 1.0)))
                self.assertTrue(pd.isna(self.gli.percent(M, 2.5, 95, E_W, param, 1.0)))

    def test_non_caucasian_returns_na(self):
        for param in [GLI_2012.Parameters.FEV075, GLI_2012.Parameters.FEV075FVC]:
            for eth in (E_B, E_NE, E_SE, E_O):
                with self.subTest(param=param.name, ethnicity=eth):
                    self.assertTrue(pd.isna(self.gli.percent(M, 5, 110, eth, param, 1.0)))


if __name__ == "__main__":
    unittest.main()

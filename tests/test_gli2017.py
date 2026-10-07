import math
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


class TestGLI2017PredictedRegression(unittest.TestCase):
    """Regression tests for the TLCO/DLCO coefficient and spline corrections.

    Expected predicted medians are the published GLI-2017 (Stanojevic 2017)
    values, independently cross-validated against the rspiro R package
    (pred_GLIdiff). These guard against the data-entry errors previously present
    in the TLCO/DLCO age coefficient (a2 sign), the TLCO/DLCO female sigma
    coefficient (p1 sign), and two mangled spline-table cells.
    """

    def setUp(self):
        self.gli = GLI_2017()

    def test_tlco_predicted_male(self):
        m = self.gli.lms(M, 40, 175, GLI_2017.Parameters.TLCO, 0)[1]
        self.assertAlmostEqual(float(m), 10.10515, places=3)

    def test_dlco_predicted_male(self):
        m = self.gli.lms(M, 40, 175, GLI_2017.Parameters.DLCO, 0)[1]
        self.assertAlmostEqual(float(m), 30.18408, places=2)

    def test_tlco_predicted_female(self):
        m = self.gli.lms(F, 40, 165, GLI_2017.Parameters.TLCO, 0)[1]
        self.assertAlmostEqual(float(m), 7.364951, places=3)

    def test_tlco_declines_with_age(self):
        # Transfer factor falls with age in adults; a positive a2 sign error
        # would (wrongly) make it rise. Guards the a2 sign.
        young = self.gli.lms(M, 30, 175, GLI_2017.Parameters.TLCO, 0)[1]
        old = self.gli.lms(M, 70, 175, GLI_2017.Parameters.TLCO, 0)[1]
        self.assertAlmostEqual(float(young), 10.68479, places=3)
        self.assertAlmostEqual(float(old), 8.396627, places=3)
        self.assertGreater(float(young), float(old))

    def test_corrected_spline_cells_finite_and_correct(self):
        # The two repaired spline cells: KCO_SI female Mspline @48.75 and
        # TLCO male Sspline @52.25 previously produced absurd/inf results.
        kco = self.gli.lms(F, 48.75, 165, GLI_2017.Parameters.KCO_SI, 0)[1]
        self.assertAlmostEqual(float(kco), 1.436139, places=3)
        z = self.gli.zscore(M, 52.25, 175, GLI_2017.Parameters.TLCO, 10.0)
        self.assertTrue(pd.notna(z))
        self.assertAlmostEqual(float(z), 0.4048955, places=3)


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


class TestGLI2017Interpolation(unittest.TestCase):
    """Splines are interpolated linearly between the quarter-year rows; closed-form terms use the exact age."""

    def setUp(self):
        self.eq = GLI_2017()

    def test_splines_interpolated_between_rows(self):
        for param in GLI_2017.Parameters:
            for sex in (M, F):
                with self.subTest(param=param.name, sex=sex):
                    lo = list(self.eq._get_splines(sex, 40.0, param))
                    hi = list(self.eq._get_splines(sex, 40.25, param))
                    age, *mid = self.eq._age_and_splines(sex, 40.1, param)
                    self.assertEqual(age, 40.1)
                    for a, b, x in zip(lo, hi, mid):
                        if pd.isna(a):
                            continue
                        self.assertAlmostEqual(x, 0.6 * a + 0.4 * b, places=12)

    def test_predicted_value_at_age_between_rows(self):
        c = self.eq._coefficients["TLCO_males"]
        _, mspline, _ = [0.6 * a + 0.4 * b for a, b in zip(self.eq._get_splines(M, 40.0, GLI_2017.Parameters.TLCO),
                                                              self.eq._get_splines(M, 40.25, GLI_2017.Parameters.TLCO))]
        expected = math.exp(c.loc["a0"] + c.loc["a1"] * math.log(170) + c.loc["a2"] * math.log(40.1) + mspline)
        _, m, _ = self.eq.lms(M, 40.1, 170, GLI_2017.Parameters.TLCO, 1.0)
        self.assertAlmostEqual(m, expected, places=12)

    def test_quarter_year_ages_use_table_row(self):
        age, *splines = self.eq._age_and_splines(M, 40.25, GLI_2017.Parameters.TLCO)
        self.assertEqual(splines, list(self.eq._get_splines(M, 40.25, GLI_2017.Parameters.TLCO)))

    def test_ages_between_rows_outside_range_return_na(self):
        low, high = self.eq._age_range
        self.assertFalse(pd.isna(self.eq.lms(M, high, 170, GLI_2017.Parameters.TLCO, 1.0)[1]))
        self.assertTrue(pd.isna(self.eq.lms(M, high + 0.1, 170, GLI_2017.Parameters.TLCO, 1.0)[1]))
        self.assertTrue(pd.isna(self.eq.lms(M, low - 0.1, 170, GLI_2017.Parameters.TLCO, 1.0)[1]))


if __name__ == "__main__":
    unittest.main()

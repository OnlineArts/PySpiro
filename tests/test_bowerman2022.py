import math
import unittest
import pandas as pd
from pyspiro import BOWERMAN_2022


M = 1
F = 0


class TestBowerman2022Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(BOWERMAN_2022())


class TestBowerman2022Percent(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_percent_known_fvc_male(self):
        # Male, 40y, 175 cm, FVC=4.5 L → 95.77%
        result = self.bow.percent(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        self.assertAlmostEqual(result, 95.77, places=1)

    def test_percent_at_median_is_100(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 0)
        result = self.bow.percent(M, 40, 175, BOWERMAN_2022.Parameters.FVC, m)
        self.assertAlmostEqual(result, 100.0, places=1)

    def test_fev1_fvc_and_fev1fvc_return_float(self):
        for param in [BOWERMAN_2022.Parameters.FEV1, BOWERMAN_2022.Parameters.FVC,
                      BOWERMAN_2022.Parameters.FEV1FVC]:
            with self.subTest(param=param.name):
                result = self.bow.percent(M, 40, 175, param, 3.0)
                self.assertFalse(pd.isna(result))

    def test_fev1fvc_female_returns_float(self):
        # FEV1FVC female splines are present in the CSV
        result = self.bow.percent(F, 40, 165, BOWERMAN_2022.Parameters.FEV1FVC, 0.78)
        self.assertFalse(pd.isna(result))

    def test_female_differs_from_male(self):
        p_m = self.bow.percent(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        p_f = self.bow.percent(F, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        self.assertNotAlmostEqual(p_m, p_f, places=1)


class TestBowerman2022ZScore(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_zscore_below_median_is_negative(self):
        # FVC=4.5 L is below median for 40yo male → negative z
        result = self.bow.zscore(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        self.assertLess(result, 0)

    def test_zscore_at_median_is_zero(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 0)
        result = self.bow.zscore(M, 40, 175, BOWERMAN_2022.Parameters.FVC, m)
        self.assertAlmostEqual(result, 0.0, places=5)


class TestBowerman2022LimitsOfNormal(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_lln_less_than_predicted(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, 0)
        lln = self.bow.lln(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, m)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, 0)
        uln = self.bow.uln(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, m)
        self.assertGreater(uln, m)

    def test_lln_zscore_is_minus_1645(self):
        lln = self.bow.lln(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, 0)
        z = self.bow.zscore(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, lln)
        self.assertAlmostEqual(z, -1.645, places=2)


class TestBowerman2022OutOfRange(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_age_out_of_range_returns_na(self):
        result = self.bow.percent(M, 200, 175, BOWERMAN_2022.Parameters.FEV1, 3.0)
        self.assertTrue(pd.isna(result))


class TestBowerman2022Interpolation(unittest.TestCase):
    """Splines are interpolated linearly between the quarter-year rows; closed-form terms use the exact age."""

    def setUp(self):
        self.eq = BOWERMAN_2022()

    def test_splines_interpolated_between_rows(self):
        for param in BOWERMAN_2022.Parameters:
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
        c = self.eq._coefficients["FEV1_males"]
        _, mspline, _ = [0.6 * a + 0.4 * b for a, b in zip(self.eq._get_splines(M, 40.0, BOWERMAN_2022.Parameters.FEV1),
                                                              self.eq._get_splines(M, 40.25, BOWERMAN_2022.Parameters.FEV1))]
        expected = math.exp(c.loc["a0"] + c.loc["a1"] * math.log(170) + c.loc["a2"] * math.log(40.1) + mspline)
        _, m, _ = self.eq.lms(M, 40.1, 170, BOWERMAN_2022.Parameters.FEV1, 1.0)
        self.assertAlmostEqual(m, expected, places=12)

    def test_quarter_year_ages_use_table_row(self):
        age, *splines = self.eq._age_and_splines(M, 40.25, BOWERMAN_2022.Parameters.FEV1)
        self.assertEqual(splines, list(self.eq._get_splines(M, 40.25, BOWERMAN_2022.Parameters.FEV1)))

    def test_ages_between_rows_outside_range_return_na(self):
        low, high = self.eq._age_range
        self.assertFalse(pd.isna(self.eq.lms(M, high, 170, BOWERMAN_2022.Parameters.FEV1, 1.0)[1]))
        self.assertTrue(pd.isna(self.eq.lms(M, high + 0.1, 170, BOWERMAN_2022.Parameters.FEV1, 1.0)[1]))
        self.assertTrue(pd.isna(self.eq.lms(M, low - 0.1, 170, BOWERMAN_2022.Parameters.FEV1, 1.0)[1]))


if __name__ == "__main__":
    unittest.main()

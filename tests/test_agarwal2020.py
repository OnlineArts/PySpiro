"""
Tests for AGARWAL_2020 — Western Indian spirometry reference values.

Cross-checks use values taken directly from the XLS supplementary lookup
tables (Supp_Tables 1–18) and from the prediction equations in Table 2 of
the paper.

Tolerances:
    Volumes (FEV1, FVC):   0.001 L  (rounding in the XLS table)
    FEV1FVC:               0.0001   (unitless ratio)
"""

import math
import unittest
import pandas
from pyspiro import AGARWAL_2020

MALE   = AGARWAL_2020.Sex.MALE.value    # 1
FEMALE = AGARWAL_2020.Sex.FEMALE.value  # 0
FEV1    = AGARWAL_2020.Parameters.FEV1.value
FVC     = AGARWAL_2020.Parameters.FVC.value
FEV1FVC = AGARWAL_2020.Parameters.FEV1FVC.value

TOL_VOL   = 0.001
TOL_RATIO = 0.0001


class TestInstantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(AGARWAL_2020())

    def test_age_range(self):
        eq = AGARWAL_2020()
        self.assertEqual(eq._age_range, (20, 80))

    def test_height_range(self):
        eq = AGARWAL_2020()
        self.assertEqual(eq._height_range, (137, 185))

    def test_parameters_enum(self):
        names = [p.name for p in AGARWAL_2020.Parameters]
        for name in ('FEV1', 'FVC', 'FEV1FVC'):
            self.assertIn(name, names)


class TestPredictedValue(unittest.TestCase):
    """Verify predicted values (50th centile) match Table 2 equations and Supp_Tables 13–18."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_male_fev1_age20_ht165(self):
        # linear: 0.402779 - 0.021695*20 + 0.019853*165 = 3.2446
        self.assertAlmostEqual(
            self.eq.percent(MALE, 20, 165, FEV1, value=3.2446), 100.0, delta=0.05)

    def test_male_fev1_age40_ht165(self):
        self.assertAlmostEqual(
            self.eq.percent(MALE, 40, 165, FEV1, value=2.8107), 100.0, delta=0.05)

    def test_male_fev1_age60_ht165(self):
        self.assertAlmostEqual(
            self.eq.percent(MALE, 60, 165, FEV1, value=2.3768), 100.0, delta=0.05)

    def test_male_fvc_age20_ht165(self):
        self.assertAlmostEqual(
            self.eq.percent(MALE, 20, 165, FVC, value=3.7765), 100.0, delta=0.05)

    def test_male_fvc_age40_ht165(self):
        self.assertAlmostEqual(
            self.eq.percent(MALE, 40, 165, FVC, value=3.4472), 100.0, delta=0.05)

    def test_male_fvc_age60_ht165(self):
        self.assertAlmostEqual(
            self.eq.percent(MALE, 60, 165, FVC, value=3.1179), 100.0, delta=0.05)

    def test_male_fev1fvc_age40(self):
        # linear: 0.922257 - 0.002695*40 = 0.81446 (height-independent)
        self.assertAlmostEqual(
            self.eq.percent(MALE, 40, 165, FEV1FVC, value=0.8145), 100.0, delta=0.05)

    def test_male_fev1fvc_height_independent(self):
        # FEV1/FVC has no height term — same pv at different heights
        pct_165 = self.eq.percent(MALE, 50, 165, FEV1FVC, value=0.7875)
        pct_170 = self.eq.percent(MALE, 50, 170, FEV1FVC, value=0.7875)
        self.assertAlmostEqual(pct_165, pct_170, delta=0.01)

    def test_female_fev1_age20_ht155(self):
        # exp: exp(-0.6439556 - 0.0066921*20 + 0.0104873*155) = 2.3344
        self.assertAlmostEqual(
            self.eq.percent(FEMALE, 20, 155, FEV1, value=2.3344), 100.0, delta=0.05)

    def test_female_fev1_age40_ht160(self):
        self.assertAlmostEqual(
            self.eq.percent(FEMALE, 40, 160, FEV1, value=2.1519), 100.0, delta=0.05)

    def test_female_fev1_age60_ht155(self):
        self.assertAlmostEqual(
            self.eq.percent(FEMALE, 60, 155, FEV1, value=1.7861), 100.0, delta=0.05)

    def test_female_fvc_age40_ht160(self):
        self.assertAlmostEqual(
            self.eq.percent(FEMALE, 40, 160, FVC, value=2.6282), 100.0, delta=0.05)

    def test_female_fvc_age60_ht155(self):
        self.assertAlmostEqual(
            self.eq.percent(FEMALE, 60, 155, FVC, value=2.2978), 100.0, delta=0.05)

    def test_female_fev1fvc_age40(self):
        # linear: 0.905877 - 0.002132*40 = 0.8206
        self.assertAlmostEqual(
            self.eq.percent(FEMALE, 40, 160, FEV1FVC, value=0.8206), 100.0, delta=0.05)


class TestLLN(unittest.TestCase):
    """Verify lln() returns the 5th centile from the lookup table."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_male_fev1_age20_ht165(self):
        self.assertAlmostEqual(
            self.eq.lln(MALE, 20, 165, FEV1), 2.5637, delta=TOL_VOL)

    def test_male_fev1_age40_ht165(self):
        self.assertAlmostEqual(
            self.eq.lln(MALE, 40, 165, FEV1), 2.1298, delta=TOL_VOL)

    def test_male_fev1_age60_ht165(self):
        self.assertAlmostEqual(
            self.eq.lln(MALE, 60, 165, FEV1), 1.6959, delta=TOL_VOL)

    def test_male_fvc_age40_ht165(self):
        self.assertAlmostEqual(
            self.eq.lln(MALE, 40, 165, FVC), 2.6685, delta=TOL_VOL)

    def test_male_fvc_age60_ht165(self):
        self.assertAlmostEqual(
            self.eq.lln(MALE, 60, 165, FVC), 2.3392, delta=TOL_VOL)

    def test_male_fev1fvc_age40_ht165(self):
        self.assertAlmostEqual(
            self.eq.lln(MALE, 40, 165, FEV1FVC), 0.7168, delta=TOL_RATIO)

    def test_male_fev1fvc_age60_ht165(self):
        self.assertAlmostEqual(
            self.eq.lln(MALE, 60, 165, FEV1FVC), 0.6629, delta=TOL_RATIO)

    def test_female_fev1_age20_ht155(self):
        self.assertAlmostEqual(
            self.eq.lln(FEMALE, 20, 155, FEV1), 1.9132, delta=TOL_VOL)

    def test_female_fev1_age40_ht160(self):
        self.assertAlmostEqual(
            self.eq.lln(FEMALE, 40, 160, FEV1), 1.6397, delta=TOL_VOL)

    def test_female_fev1_age60_ht155(self):
        self.assertAlmostEqual(
            self.eq.lln(FEMALE, 60, 155, FEV1), 1.2560, delta=TOL_VOL)

    def test_female_fvc_age40_ht160(self):
        self.assertAlmostEqual(
            self.eq.lln(FEMALE, 40, 160, FVC), 2.0393, delta=TOL_VOL)

    def test_female_fev1fvc_age40(self):
        self.assertAlmostEqual(
            self.eq.lln(FEMALE, 40, 160, FEV1FVC), 0.7211, delta=TOL_RATIO)

    def test_lln_below_predicted_across_ages(self):
        for sex, ht in ((MALE, 165), (FEMALE, 155)):
            for age in (25, 45, 65):
                for param in (FEV1, FVC, FEV1FVC):
                    with self.subTest(sex=sex, age=age, param=param):
                        lln = self.eq.lln(sex, age, ht, param)
                        pct = self.eq.percent(sex, age, ht, param, value=lln)
                        self.assertLess(pct, 100.0)


class TestULN(unittest.TestCase):
    """Verify uln() = 2*pv - p5 and lies above the predicted median."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_male_fev1_age40_ht165(self):
        # pv=2.8107, p5=2.1298 → uln=3.4916
        self.assertAlmostEqual(
            self.eq.uln(MALE, 40, 165, FEV1), 3.4916, delta=TOL_VOL)

    def test_male_fvc_age20_ht165(self):
        # pv=3.7765, p5=2.9978 → uln=4.5552
        self.assertAlmostEqual(
            self.eq.uln(MALE, 20, 165, FVC), 4.5552, delta=TOL_VOL)

    def test_male_fev1fvc_age60_ht165(self):
        # pv=0.7606, p5=0.6629 → uln=0.8582
        self.assertAlmostEqual(
            self.eq.uln(MALE, 60, 165, FEV1FVC), 0.8582, delta=TOL_RATIO)

    def test_female_fev1_age40_ht160(self):
        # pv=2.1519, p5=1.6397 → uln=2.6640
        self.assertAlmostEqual(
            self.eq.uln(FEMALE, 40, 160, FEV1), 2.6640, delta=TOL_VOL)

    def test_female_fvc_age40_ht160(self):
        # pv=2.6282, p5=2.0393 → uln=3.2172
        self.assertAlmostEqual(
            self.eq.uln(FEMALE, 40, 160, FVC), 3.2172, delta=TOL_VOL)

    def test_uln_above_predicted(self):
        for sex, ht in ((MALE, 165), (FEMALE, 155)):
            for age in (25, 45, 65):
                for param in (FEV1, FVC, FEV1FVC):
                    with self.subTest(sex=sex, age=age, param=param):
                        pct = self.eq.percent(
                            sex, age, ht, param,
                            value=self.eq.uln(sex, age, ht, param))
                        self.assertGreater(pct, 100.0)

    def test_symmetric_around_pv(self):
        # uln - pv == pv - lln (symmetry by construction)
        pv  = 2.8107  # male FEV1 age=40 ht=165
        lln = self.eq.lln(MALE, 40, 165, FEV1)
        uln = self.eq.uln(MALE, 40, 165, FEV1)
        self.assertAlmostEqual(uln - pv, pv - lln, delta=1e-4)


class TestPercent(unittest.TestCase):
    """Spot-checks for the percent() method."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_at_pv_gives_100(self):
        self.assertAlmostEqual(
            self.eq.percent(MALE, 40, 165, FEV1, value=2.8107), 100.0, delta=0.05)

    def test_explicit_male_fev1(self):
        # pv=2.8107, value=2.5: expected = 2.5/2.8107 * 100 = 88.95
        expected = round(2.5 / 2.8107 * 100, 2)
        self.assertAlmostEqual(
            self.eq.percent(MALE, 40, 165, FEV1, value=2.5), expected, delta=0.05)

    def test_explicit_female_fev1(self):
        # pv=1.7861, value=1.5
        expected = round(1.5 / 1.7861 * 100, 2)
        self.assertAlmostEqual(
            self.eq.percent(FEMALE, 60, 155, FEV1, value=1.5), expected, delta=0.1)


class TestZscore(unittest.TestCase):
    """Verify z-score: (value - pv) / ((pv - p5) / 1.645), normal approximation."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_at_pv_zscore_zero(self):
        self.assertAlmostEqual(
            self.eq.zscore(MALE, 40, 165, FEV1, value=2.8107), 0.0, delta=0.01)

    def test_at_lln_zscore_minus_1645_male(self):
        lln = self.eq.lln(MALE, 40, 165, FEV1)
        z   = self.eq.zscore(MALE, 40, 165, FEV1, value=lln)
        self.assertAlmostEqual(z, -1.645, delta=0.01)

    def test_at_lln_zscore_minus_1645_female(self):
        lln = self.eq.lln(FEMALE, 40, 160, FEV1)
        z   = self.eq.zscore(FEMALE, 40, 160, FEV1, value=lln)
        self.assertAlmostEqual(z, -1.645, delta=0.01)

    def test_explicit_value_male_fev1(self):
        # pv=2.8107, p5=2.1298 → see=(2.8107-2.1298)/1.645=0.41384
        # z = (2.5 - 2.8107) / 0.41384 = -0.7506
        z = self.eq.zscore(MALE, 40, 165, FEV1, value=2.5)
        self.assertAlmostEqual(z, -0.7506, delta=0.01)


class TestLMS(unittest.TestCase):
    """lms() is not applicable for this equation; must return (NA, NA, NA)."""

    def test_returns_na_triple(self):
        eq = AGARWAL_2020()
        l, m, s = eq.lms(MALE, 40, 165, FEV1)
        self.assertIs(l, pandas.NA)
        self.assertIs(m, pandas.NA)
        self.assertIs(s, pandas.NA)


class TestOutOfRange(unittest.TestCase):
    """Out-of-range inputs must return pandas.NA (default 'ignore' strategy)."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_age_too_low(self):
        self.assertIs(self.eq.lln(MALE, 19, 165, FEV1), pandas.NA)

    def test_age_too_high(self):
        self.assertIs(self.eq.lln(MALE, 81, 165, FEV1), pandas.NA)

    def test_height_too_low(self):
        self.assertIs(self.eq.lln(MALE, 40, 136, FEV1), pandas.NA)

    def test_height_too_high(self):
        self.assertIs(self.eq.lln(MALE, 40, 186, FEV1), pandas.NA)

    def test_percent_out_of_range_age(self):
        self.assertIs(self.eq.percent(MALE, 19, 165, FEV1, 2.5), pandas.NA)

    def test_zscore_out_of_range_height(self):
        self.assertIs(self.eq.zscore(FEMALE, 40, 200, FEV1, 2.0), pandas.NA)

    def test_boundary_age_low_valid(self):
        self.assertIsNotNone(self.eq.lln(MALE, 20, 165, FEV1))
        self.assertIsNot(self.eq.lln(MALE, 20, 165, FEV1), pandas.NA)

    def test_boundary_age_high_valid(self):
        self.assertIsNot(self.eq.lln(MALE, 80, 165, FEV1), pandas.NA)

    def test_boundary_height_low_valid(self):
        self.assertIsNot(self.eq.lln(MALE, 40, 137, FEV1), pandas.NA)

    def test_boundary_height_high_valid(self):
        self.assertIsNot(self.eq.lln(MALE, 40, 185, FEV1), pandas.NA)


class TestRounding(unittest.TestCase):
    """Float inputs should round to the nearest integer for lookup."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_age_rounded_down(self):
        self.assertEqual(
            self.eq.lln(MALE, 40.4, 165, FEV1),
            self.eq.lln(MALE, 40,   165, FEV1))

    def test_age_rounded_up(self):
        self.assertEqual(
            self.eq.lln(MALE, 40.6, 165, FEV1),
            self.eq.lln(MALE, 41,   165, FEV1))

    def test_height_rounded_down(self):
        self.assertEqual(
            self.eq.lln(MALE, 40, 165.4, FEV1),
            self.eq.lln(MALE, 40, 165,   FEV1))

    def test_height_rounded_up(self):
        self.assertEqual(
            self.eq.lln(MALE, 40, 165.6, FEV1),
            self.eq.lln(MALE, 40, 166,   FEV1))


class TestAll(unittest.TestCase):
    """all() must return the same values as individual methods."""

    def setUp(self):
        self.eq = AGARWAL_2020()

    def test_all_consistent_with_individual_methods(self):
        sex, age, ht, param, value = MALE, 40, 165, FEV1, 2.5
        pct, z, lln, uln = self.eq.all(sex, age, ht, param, value)
        self.assertAlmostEqual(pct, self.eq.percent(sex, age, ht, param, value), places=6)
        self.assertAlmostEqual(z,   self.eq.zscore(sex, age, ht, param, value),  places=6)
        self.assertAlmostEqual(lln, self.eq.lln(sex, age, ht, param),             places=6)
        self.assertAlmostEqual(uln, self.eq.uln(sex, age, ht, param),             places=6)

    def test_all_out_of_range_returns_na(self):
        result = self.eq.all(MALE, 90, 165, FEV1, 2.5)
        self.assertTrue(all(v is pandas.NA for v in result))


if __name__ == '__main__':
    unittest.main()

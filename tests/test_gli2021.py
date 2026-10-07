import math
import unittest
import pandas as pd
from pyspiro import GLI_2021


M = 1
F = 0


class TestGLI2021Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(GLI_2021())

    def test_age_range(self):
        gli = GLI_2021()
        self.assertEqual(gli._age_range[0], 5)
        self.assertEqual(gli._age_range[1], 80)


class TestGLI2021Structural(unittest.TestCase):
    """
    Structural tests that verify correct LMS mechanics regardless of the
    absolute coefficient values in the CSV.
    """

    def setUp(self):
        self.gli = GLI_2021()

    def test_lms_returns_three_tuple(self):
        result = self.gli.lms(M, 40, 175, GLI_2021.Parameters.TLC, 0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_percent_at_median_is_100(self):
        for param in GLI_2021.Parameters:
            with self.subTest(param=param.name):
                l, m, s = self.gli.lms(M, 40, 175, param, 0)
                if pd.isna(m):
                    continue
                result = self.gli.percent(M, 40, 175, param, m)
                self.assertAlmostEqual(result, 100.0, places=1)

    def test_zscore_at_median_is_zero(self):
        l, m, s = self.gli.lms(M, 40, 175, GLI_2021.Parameters.TLC, 0)
        if pd.isna(m):
            self.skipTest("lms returned NA")
        result = self.gli.zscore(M, 40, 175, GLI_2021.Parameters.TLC, m)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_lln_less_than_predicted(self):
        l, m, s = self.gli.lms(M, 40, 175, GLI_2021.Parameters.TLC, 0)
        if pd.isna(m):
            self.skipTest("lms returned NA")
        lln = self.gli.lln(M, 40, 175, GLI_2021.Parameters.TLC, m)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted(self):
        l, m, s = self.gli.lms(M, 40, 175, GLI_2021.Parameters.TLC, 0)
        if pd.isna(m):
            self.skipTest("lms returned NA")
        uln = self.gli.uln(M, 40, 175, GLI_2021.Parameters.TLC, m)
        self.assertGreater(uln, m)

    def test_female_differs_from_male(self):
        l_m, m_m, s_m = self.gli.lms(M, 40, 175, GLI_2021.Parameters.TLC, 0)
        l_f, m_f, s_f = self.gli.lms(F, 40, 175, GLI_2021.Parameters.TLC, 0)
        self.assertNotAlmostEqual(m_m, m_f, places=3)


class TestGLI2021OutOfRange(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2021()

    def test_age_below_range_returns_na(self):
        result = self.gli.percent(M, 4, 175, GLI_2021.Parameters.TLC, 7.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.gli.percent(M, 81, 175, GLI_2021.Parameters.TLC, 7.0)
        self.assertTrue(pd.isna(result))


class TestGLI2021ReferenceValues(unittest.TestCase):
    """
    Validation against the authoritative predicted values published by
    Hall et al. 2021 (ERJ 57:2000289). These pin the absolute calibration of
    each equation, unlike the purely structural tests above. Hall's table 3
    uses parameter-specific predictor transforms (FRC/TLC use log(age) &
    log(height); RV & RV/TLC use linear age & height; ERV/IC/VC use linear age
    & log(height)), which must be reproduced exactly.
    """

    def setUp(self):
        self.gli = GLI_2021()

    def test_worked_example_frc(self):
        # Supplement 1, "Worked Example for FRC": male, 30 y, 178 cm, FRC = 3.7 L.
        l, m, s = self.gli.lms(M, 30, 178, GLI_2021.Parameters.FRC, 0)
        self.assertAlmostEqual(float(m), 3.307587, places=5)
        self.assertAlmostEqual(float(s), 0.2190672, places=6)
        self.assertAlmostEqual(float(l), 0.3416, places=4)
        self.assertAlmostEqual(float(self.gli.percent(M, 30, 178, GLI_2021.Parameters.FRC, 3.7)), 111.864, places=1)
        self.assertAlmostEqual(float(self.gli.lln(M, 30, 178, GLI_2021.Parameters.FRC, 3.7)), 2.251922, places=3)
        self.assertAlmostEqual(float(self.gli.zscore(M, 30, 178, GLI_2021.Parameters.FRC, 3.7)), 0.5211515, places=2)

    def test_table_s3_predicted_values(self):
        # Supplement 1, table S3 "Male, 1.75 m, 40 y", final (all-observations) equations.
        expected = {
            GLI_2021.Parameters.FRC: 3.183,
            GLI_2021.Parameters.TLC: 6.915,
            GLI_2021.Parameters.RV: 1.533,
        }
        for param, pred in expected.items():
            with self.subTest(param=param.name):
                m = float(self.gli.lms(M, 40, 175, param, 0)[1])
                # within 1.5 % of the published table value
                self.assertAlmostEqual(m / pred, 1.0, delta=0.015)

    def test_absolute_volumes_are_physiological(self):
        # Guards against the historical bug where every predicted median
        # collapsed by ~25x (e.g. TLC ~0.28 L) due to swapped/log-misapplied
        # age & height predictors.
        ranges = {  # male, 40 y, 175 cm
            GLI_2021.Parameters.FRC: (2.5, 4.5),
            GLI_2021.Parameters.TLC: (5.5, 8.0),
            GLI_2021.Parameters.RV: (1.0, 2.5),
            GLI_2021.Parameters.RV_TLC: (18.0, 30.0),  # percent
            GLI_2021.Parameters.ERV: (0.8, 2.5),
            GLI_2021.Parameters.IC: (2.5, 4.5),
            GLI_2021.Parameters.VC: (4.0, 6.5),
        }
        for param, (lo, hi) in ranges.items():
            with self.subTest(param=param.name):
                m = float(self.gli.lms(M, 40, 175, param, 0)[1])
                self.assertTrue(lo <= m <= hi, f"{param.name} predicted {m:.3f} outside [{lo}, {hi}]")

    def test_rv_tlc_zscore_uses_percent_scale(self):
        # RV/TLC is modelled in percent (~22 % predicted here); a healthy ratio
        # entered as a percentage must give a moderate z-score, not z<-3.
        z = float(self.gli.zscore(M, 40, 175, GLI_2021.Parameters.RV_TLC, 30.0))
        self.assertTrue(-1.0 < z < 3.0)


class TestGLI2021Table3Exact(unittest.TestCase):
    """
    Exact check against Hall et al. 2021 (ERJ 57:2000289), Table 3, evaluated by
    hand with the age-varying Mspline/Sspline values of the published look-up
    tables (supplementary material 2, inline-supplementary-material-2.xlsx).
    All seven indices, male 40 y 175 cm and female 60 y 162 cm. The coefficients
    and spline values below are literals copied from the paper/workbook, so the
    test does not depend on pyspiro/data.

    Note: Supplement 1, table S3 lists RV = 1.533 L for a 40-year-old 175 cm male,
    whereas Table 3 with the published look-up table gives 1.5526 L, and the
    official GLI calculator returns 1.553 L for the same input. The table S3 value
    is therefore a probable typographical error (1.553 -> 1.533). PySpiro follows
    Table 3.
    """

    # (M equation, S equation, L) from Table 3; ms/ss = Mspline/Sspline at the case age
    CASES = [
        # sex, age, height, parameter, M(age, ht, ms), S(age, ss), L, ms, ss
        (M, 40, 175, "FRC", lambda a, h, ms: math.exp(-13.4898 + 0.1111 * math.log(a) + 2.7634 * math.log(h) + ms),
         lambda a, ss: math.exp(-1.60197 + 0.01513 * math.log(a) + ss), 0.3416,
         -0.0346783008046163, 0.0271613631819752),
        (M, 40, 175, "TLC", lambda a, h, ms: math.exp(-10.5861 + 0.1433 * math.log(a) + 2.3155 * math.log(h) + ms),
         lambda a, ss: math.exp(-2.0616143 - 0.0008534 * a + ss), 0.9337,
         0.0318859822724828, -0.0469374292404532),
        (M, 40, 175, "RV", lambda a, h, ms: math.exp(-2.37211 + 0.01346 * a + 0.01307 * h + ms),
         lambda a, ss: math.exp(-0.878572 - 0.007032 * a + ss), 0.5931,
         -0.0136063778815025, -0.00636014426010312),
        (M, 40, 175, "RV_TLC", lambda a, h, ms: math.exp(2.634 + 0.01302 * a - 0.00008862 * h + ms),
         lambda a, ss: math.exp(-0.96804 - 0.01004 * a + ss), 0.8646,
         -0.0343075571987033, -0.00404147561534751),
        (M, 40, 175, "ERV", lambda a, h, ms: math.exp(-17.328650 - 0.006288 * a + 3.478116 * math.log(h) + ms),
         lambda a, ss: math.exp(-1.307616 + 0.009177 * a), 0.5517, 0.0279636177678171, 0.0),
        (M, 40, 175, "IC", lambda a, h, ms: math.exp(-10.121688 + 0.001265 * a + 2.188801 * math.log(h) + ms),
         lambda a, ss: math.exp(-1.856546 + 0.002008 * a), 1.146, 0.0865356453467374, 0.0),
        (M, 40, 175, "VC", lambda a, h, ms: math.exp(-10.134371 - 0.003532 * a + 2.307980 * math.log(h) + ms),
         lambda a, ss: math.exp(-2.1367411 + 0.0009367 * a), 0.8611, 0.0362506609552984, 0.0),
        (F, 60, 162, "FRC", lambda a, h, ms: math.exp(-12.7674 + 0.1251 * math.log(a) + 2.6049 * math.log(h) + ms),
         lambda a, ss: math.exp(-1.48310 - 0.03372 * math.log(a) + ss), 0.2898,
         -0.00867006307005092, 0.00114727066128206),
        (F, 60, 162, "TLC", lambda a, h, ms: math.exp(-10.1128 + 0.1062 * math.log(a) + 2.2259 * math.log(h) + ms),
         lambda a, ss: math.exp(-2.0999321 + 0.0001564 * a + ss), 0.4636,
         -0.0232888415469912, -0.00339370668009664),
        (F, 60, 162, "RV", lambda a, h, ms: math.exp(-2.50593 + 0.01307 * a + 0.01379 * h + ms),
         lambda a, ss: math.exp(-0.902550 - 0.006005 * a + ss), 0.4197,
         0.023598070842455, -0.0404415051253932),
        (F, 60, 162, "RV_TLC", lambda a, h, ms: math.exp(2.666 + 0.01411 * a - 0.00003689 * h + ms),
         lambda a, ss: math.exp(-0.976602 - 0.009679 * a + ss), 0.8037,
         -0.00186003227991938, -0.0247551739326295),
        (F, 60, 162, "ERV", lambda a, h, ms: math.exp(-14.145513 - 0.009573 * a + 2.871446 * math.log(h) + ms),
         lambda a, ss: math.exp(-1.54992 + 0.01409 * a), 0.5326, -0.0717122533204559, 0.0),
        (F, 60, 162, "IC", lambda a, h, ms: math.exp(-9.4438787 - 0.0002484 * a + 2.0312769 * math.log(h) + ms),
         lambda a, ss: math.exp(-1.775276 + 0.002673 * a), 0.9726, 0.0208265870779449, 0.0),
        (F, 60, 162, "VC", lambda a, h, ms: math.exp(-9.230600 - 0.005517 * a + 2.116822 * math.log(h) + ms),
         lambda a, ss: math.exp(-2.220260 + 0.002956 * a), 1.038, 0.00949220131507822, 0.0),
    ]

    def setUp(self):
        self.gli = GLI_2021()

    def test_lms_matches_table3(self):
        for sex, age, h, p, m_eq, s_eq, l_ref, ms, ss in self.CASES:
            with self.subTest(sex=sex, parameter=p):
                l, m, s = self.gli.lms(sex, age, h, GLI_2021.Parameters[p], 0)
                self.assertAlmostEqual(float(m), m_eq(age, h, ms), places=10)
                self.assertAlmostEqual(float(s), s_eq(age, ss), places=10)
                self.assertAlmostEqual(float(l), l_ref, places=10)

    def test_rv_male_40_175_predicted(self):
        # Table 3 by hand: exp(-2.37211 + 0.01346*40 + 0.01307*175 - 0.0136063778815025)
        m = self.gli.lms(M, 40, 175, GLI_2021.Parameters.RV, 0)[1]
        self.assertAlmostEqual(float(m), 1.5526041565, places=8)

class TestGLI2021Interpolation(unittest.TestCase):
    """Splines are interpolated linearly between the quarter-year rows; closed-form terms use the exact age."""

    def setUp(self):
        self.eq = GLI_2021()

    def test_splines_interpolated_between_rows(self):
        for param in GLI_2021.Parameters:
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
        c = self.eq._coefficients["FRC_males"]
        _, mspline, _ = [0.6 * a + 0.4 * b for a, b in zip(self.eq._get_splines(M, 40.0, GLI_2021.Parameters.FRC),
                                                              self.eq._get_splines(M, 40.25, GLI_2021.Parameters.FRC))]
        expected = math.exp(c.loc["a0"] + c.loc["a1"] * math.log(40.1) + c.loc["a2"] * math.log(170) + mspline)
        _, m, _ = self.eq.lms(M, 40.1, 170, GLI_2021.Parameters.FRC, 1.0)
        self.assertAlmostEqual(m, expected, places=12)

    def test_quarter_year_ages_use_table_row(self):
        age, *splines = self.eq._age_and_splines(M, 40.25, GLI_2021.Parameters.FRC)
        self.assertEqual(splines, list(self.eq._get_splines(M, 40.25, GLI_2021.Parameters.FRC)))

    def test_ages_between_rows_outside_range_return_na(self):
        low, high = self.eq._age_range
        self.assertFalse(pd.isna(self.eq.lms(M, high, 170, GLI_2021.Parameters.FRC, 1.0)[1]))
        self.assertTrue(pd.isna(self.eq.lms(M, high + 0.1, 170, GLI_2021.Parameters.FRC, 1.0)[1]))
        self.assertTrue(pd.isna(self.eq.lms(M, low - 0.1, 170, GLI_2021.Parameters.FRC, 1.0)[1]))

if __name__ == "__main__":
    unittest.main()

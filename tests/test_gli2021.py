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


if __name__ == "__main__":
    unittest.main()

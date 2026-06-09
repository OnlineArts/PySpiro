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


if __name__ == "__main__":
    unittest.main()

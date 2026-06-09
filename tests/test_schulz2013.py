import unittest
import pandas as pd
from pyspiro import SCHULZ_2013


M = 1
F = 0


class TestSchulz2013Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(SCHULZ_2013())


class TestSchulz2013Percentiles(unittest.TestCase):

    def setUp(self):
        self.s = SCHULZ_2013()

    def test_percentiles_returns_three_tuple(self):
        result = self.s.percentiles(M, 60, 175, 80, SCHULZ_2013.Parameters.X10)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_percentiles_ordered(self):
        p5, p50, p95 = self.s.percentiles(M, 60, 175, 80, SCHULZ_2013.Parameters.X10)
        self.assertLess(p5, p50)
        self.assertLess(p50, p95)

    def test_all_parameters_return_float(self):
        for param in SCHULZ_2013.Parameters:
            with self.subTest(param=param.name):
                p5, p50, p95 = self.s.percentiles(M, 60, 175, 80, param)
                self.assertIsInstance(p5, float)
                self.assertIsInstance(p50, float)
                self.assertIsInstance(p95, float)

    def test_female_differs_from_male(self):
        p5_m, p50_m, _ = self.s.percentiles(M, 60, 175, 80, SCHULZ_2013.Parameters.R10)
        p5_f, p50_f, _ = self.s.percentiles(F, 60, 165, 70, SCHULZ_2013.Parameters.R10)
        self.assertNotAlmostEqual(p50_m, p50_f, places=3)


class TestSchulz2013LLNAndULN(unittest.TestCase):

    def setUp(self):
        self.s = SCHULZ_2013()

    def test_lln_known_value_x10_male(self):
        # Male, 60y, 175 cm, 80 kg, X10 → LLN (p5) ≈ -0.068
        result = self.s.lln(M, 60, 175, 80, SCHULZ_2013.Parameters.X10, None)
        self.assertAlmostEqual(result, -0.068, places=2)

    def test_uln_known_value_x10_male(self):
        # Male, 60y, 175 cm, 80 kg, X10 → ULN (p95) ≈ 0.021
        result = self.s.uln(M, 60, 175, 80, SCHULZ_2013.Parameters.X10, None)
        self.assertAlmostEqual(result, 0.021, places=2)

    def test_lln_equals_p5(self):
        p5, p50, p95 = self.s.percentiles(M, 60, 175, 80, SCHULZ_2013.Parameters.R10)
        lln = self.s.lln(M, 60, 175, 80, SCHULZ_2013.Parameters.R10, None)
        self.assertAlmostEqual(lln, p5, places=6)

    def test_uln_equals_p95(self):
        p5, p50, p95 = self.s.percentiles(M, 60, 175, 80, SCHULZ_2013.Parameters.R10)
        uln = self.s.uln(M, 60, 175, 80, SCHULZ_2013.Parameters.R10, None)
        self.assertAlmostEqual(uln, p95, places=6)

    def test_lln_less_than_uln(self):
        lln = self.s.lln(M, 60, 175, 80, SCHULZ_2013.Parameters.R10, None)
        uln = self.s.uln(M, 60, 175, 80, SCHULZ_2013.Parameters.R10, None)
        self.assertLess(lln, uln)


class TestSchulz2013NotImplemented(unittest.TestCase):

    def setUp(self):
        self.s = SCHULZ_2013()

    def test_percent_not_implemented_returns_none(self):
        result = self.s.percent(M, 60, 175, SCHULZ_2013.Parameters.R10, 0.5)
        self.assertIsNone(result)

    def test_zscore_not_implemented_returns_none(self):
        result = self.s.zscore(M, 60, 175, SCHULZ_2013.Parameters.R10, 0.5)
        self.assertIsNone(result)


class TestSchulz2013All(unittest.TestCase):

    def setUp(self):
        self.s = SCHULZ_2013()

    def test_all_returns_three_tuple(self):
        result = self.s.all(M, 60, 175, 80, SCHULZ_2013.Parameters.R10, None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_all_equals_lln_median_uln(self):
        p5, p50, p95 = self.s.percentiles(M, 60, 175, 80, SCHULZ_2013.Parameters.R10)
        a1, a2, a3 = self.s.all(M, 60, 175, 80, SCHULZ_2013.Parameters.R10, None)
        self.assertAlmostEqual(a1, p5, places=6)
        self.assertAlmostEqual(a2, p50, places=6)
        self.assertAlmostEqual(a3, p95, places=6)


if __name__ == "__main__":
    unittest.main()

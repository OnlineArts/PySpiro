import unittest
import pandas as pd
from pyspiro import KUSTER_2008


M = 1
F = 0


class TestKuster2008Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(KUSTER_2008())

    def test_age_range(self):
        k = KUSTER_2008()
        self.assertEqual(k._age_range, (18, 80))

    def test_height_ranges(self):
        k = KUSTER_2008()
        self.assertEqual(k._height_male_range, (140, 200))
        self.assertEqual(k._height_female_range, (130, 190))


class TestKuster2008Percent(unittest.TestCase):

    def setUp(self):
        self.k = KUSTER_2008()

    def test_percent_known_fev1_male(self):
        # Male, 40y, 175 cm, FEV1=3.5 L → 87.24%
        result = self.k.percent(M, 40, 175, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        self.assertAlmostEqual(result, 87.24, places=1)

    def test_percent_returns_float_male(self):
        for param in [KUSTER_2008.Parameters.FVC, KUSTER_2008.Parameters.FEV1,
                      KUSTER_2008.Parameters.MEF75, KUSTER_2008.Parameters.MEF50,
                      KUSTER_2008.Parameters.MEF25, KUSTER_2008.Parameters.FEV1_FVC_P,
                      KUSTER_2008.Parameters.PEF]:
            with self.subTest(param=param.name):
                result = self.k.percent(M, 40, 175, 1, param, 3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_percent_returns_float_female(self):
        for param in [KUSTER_2008.Parameters.FVC, KUSTER_2008.Parameters.FEV1,
                      KUSTER_2008.Parameters.MEF75, KUSTER_2008.Parameters.MEF50,
                      KUSTER_2008.Parameters.MEF25, KUSTER_2008.Parameters.FEV1_FVC_P,
                      KUSTER_2008.Parameters.PEF]:
            with self.subTest(param=param.name):
                result = self.k.percent(F, 40, 165, 1, param, 3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_female_differs_from_male(self):
        p_m = self.k.percent(M, 40, 175, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        p_f = self.k.percent(F, 40, 165, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        self.assertNotAlmostEqual(p_m, p_f, places=1)


class TestKuster2008LLN(unittest.TestCase):

    def setUp(self):
        self.k = KUSTER_2008()

    def test_lln_returns_float(self):
        result = self.k.lln(M, 40, 175, 1, KUSTER_2008.Parameters.FEV1_LLN, 3.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_lln_less_than_predicted(self):
        predicted_m = self.k.percent(M, 40, 175, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        lln = self.k.lln(M, 40, 175, 1, KUSTER_2008.Parameters.FEV1_LLN, 3.5)
        # LLN should be a smaller absolute value than the predicted FEV1
        # (i.e., the threshold below which is abnormal)
        pred_fvc = self.k.percent(M, 40, 175, 1, KUSTER_2008.Parameters.FVC, 4.0)
        pred_abs = 4.0 / (pred_fvc / 100)   # predicted FVC in litres
        lln_fvc = self.k.lln(M, 40, 175, 1, KUSTER_2008.Parameters.FVC_LLN, 4.0)
        self.assertLess(lln_fvc, pred_abs)

    def test_all_lln_parameters_return_float(self):
        for param in [KUSTER_2008.Parameters.FVC_LLN, KUSTER_2008.Parameters.FEV1_LLN,
                      KUSTER_2008.Parameters.MEF75_LLN, KUSTER_2008.Parameters.MEF50_LLN,
                      KUSTER_2008.Parameters.MEF25_LLN, KUSTER_2008.Parameters.FEV1_FVC_LLN,
                      KUSTER_2008.Parameters.PEF_LLN]:
            with self.subTest(param=param.name):
                result = self.k.lln(M, 40, 175, 1, param, 3.0)
                self.assertFalse(pd.isna(result))


class TestKuster2008ULN(unittest.TestCase):

    def setUp(self):
        self.k = KUSTER_2008()

    def test_uln_not_implemented_returns_na(self):
        result = self.k.uln(M, 40, 175, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        self.assertTrue(pd.isna(result))


class TestKuster2008OutOfRange(unittest.TestCase):

    def setUp(self):
        self.k = KUSTER_2008()

    def test_age_below_range_returns_na(self):
        result = self.k.percent(M, 17, 175, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.k.percent(M, 81, 175, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        self.assertTrue(pd.isna(result))

    def test_height_above_male_range_returns_na(self):
        result = self.k.percent(M, 40, 201, 1, KUSTER_2008.Parameters.FEV1, 3.5)
        self.assertTrue(pd.isna(result))

    def test_height_below_female_range_returns_na(self):
        result = self.k.percent(F, 40, 129, 1, KUSTER_2008.Parameters.FEV1, 2.5)
        self.assertTrue(pd.isna(result))


if __name__ == "__main__":
    unittest.main()

import unittest
import pandas as pd
from pyspiro import SCAPIS_2023


M = 1
F = 0


class TestSCAPIS2023Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(SCAPIS_2023())

    def test_age_range(self):
        s = SCAPIS_2023()
        self.assertGreaterEqual(s._age_range[0], 50)
        self.assertLessEqual(s._age_range[1], 65)


class TestSCAPIS2023Percent(unittest.TestCase):

    def setUp(self):
        self.scapis = SCAPIS_2023()

    def test_percent_at_median_is_100(self):
        l, m, s = self.scapis.lms(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 0)
        result = self.scapis.percent(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, m)
        self.assertAlmostEqual(result, 100.0, places=1)

    def test_all_parameters_return_float(self):
        for param in SCAPIS_2023.Parameters:
            with self.subTest(param=param.name):
                result = self.scapis.percent(M, 55, 175, param, 3.0)
                self.assertFalse(pd.isna(result))

    def test_female_differs_from_male(self):
        p_m = self.scapis.percent(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 3.0)
        p_f = self.scapis.percent(F, 55, 165, SCAPIS_2023.Parameters.pre_BD_FEV1, 3.0)
        self.assertNotAlmostEqual(p_m, p_f, places=1)


class TestSCAPIS2023LimitsOfNormal(unittest.TestCase):

    def setUp(self):
        self.scapis = SCAPIS_2023()

    def test_lln_known_value(self):
        # Male, 55y, 175 cm, pre-BD FEV1=3.0 L → LLN ≈ 2.884
        result = self.scapis.lln(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 3.0)
        self.assertAlmostEqual(result, 2.884, places=2)

    def test_lln_less_than_predicted(self):
        l, m, s = self.scapis.lms(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 0)
        lln = self.scapis.lln(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, m)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted(self):
        l, m, s = self.scapis.lms(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 0)
        uln = self.scapis.uln(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, m)
        self.assertGreater(uln, m)

    def test_lln_zscore_is_minus_1645(self):
        lln = self.scapis.lln(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 0)
        z = self.scapis.zscore(M, 55, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, lln)
        self.assertAlmostEqual(z, -1.645, places=2)


class TestSCAPIS2023OutOfRange(unittest.TestCase):

    def setUp(self):
        self.scapis = SCAPIS_2023()

    def test_age_below_range_returns_na(self):
        result = self.scapis.percent(M, 40, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 3.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.scapis.percent(M, 70, 175, SCAPIS_2023.Parameters.pre_BD_FEV1, 3.0)
        self.assertTrue(pd.isna(result))


if __name__ == "__main__":
    unittest.main()

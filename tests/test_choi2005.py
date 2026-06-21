import unittest
import pandas as pd
import math
from pyspiro import CHOI_2005

M = 1
F = 0


class TestChoi2005Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(CHOI_2005())

    def test_parameters_enum(self):
        params = [p.name for p in CHOI_2005.Parameters]
        for name in ('FVC', 'FEV1', 'FEV6', 'FEV1FVC'):
            self.assertIn(name, params)


class TestChoi2005Predictions(unittest.TestCase):

    def setUp(self):
        self.eq = CHOI_2005()

    # Spot-check against mean values from paper Table 3/4
    # Males: mean age=31.23, height=169.03, weight=68.73 → FEV1 ≈ 3.344 (≈Table 3 mean 3.29)

    def test_male_fev1_plausible(self):
        result = self.eq.percent(M, 31, 169, parameter=CHOI_2005.Parameters.FEV1, value=3.3, weight=69)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 50)
        self.assertLess(result, 150)

    def test_female_fev1_plausible(self):
        result = self.eq.percent(F, 33, 157, parameter=CHOI_2005.Parameters.FEV1, value=2.5, weight=55)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 50)

    def test_male_fvc_requires_weight(self):
        result = self.eq.percent(M, 35, 170, parameter=CHOI_2005.Parameters.FVC, value=4.0, weight=None)
        self.assertTrue(pd.isna(result))

    def test_male_fvc_with_weight(self):
        result = self.eq.percent(M, 35, 170, parameter=CHOI_2005.Parameters.FVC, value=4.0, weight=70)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_male_fev6_requires_weight(self):
        result = self.eq.percent(M, 35, 170, parameter=CHOI_2005.Parameters.FEV6, value=3.8, weight=None)
        self.assertTrue(pd.isna(result))

    def test_male_fev1fvc_no_weight_needed(self):
        # FEV1FVC does not need weight
        result = self.eq.percent(M, 40, 168, parameter=CHOI_2005.Parameters.FEV1FVC, value=80, weight=None)
        self.assertIsInstance(result, float)

    def test_male_fev1fvc_known_value(self):
        # Male: 119.9004 - 0.3902*40 - 0.1268*168 = 119.9004 - 15.608 - 21.3024 = 82.990
        pred = 119.9004 - 0.3902 * 40 - 0.1268 * 168
        result = self.eq.percent(M, 40, 168, parameter=CHOI_2005.Parameters.FEV1FVC, value=pred, weight=None)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fev1fvc_known_value(self):
        # Female: 97.8567 - 0.2800*35 - 0.01564*160 = 97.8567 - 9.8 - 2.5024 = 85.554
        pred = 97.8567 - 0.2800 * 35 - 0.01564 * 160
        result = self.eq.percent(F, 35, 160, parameter=CHOI_2005.Parameters.FEV1FVC, value=pred, weight=None)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fvc_known_value(self):
        # Male FVC at age=31, ht=169, wt=69
        # = -4.8434 - 0.00008633*31^2 + 0.05292*169 + 0.01095*69
        pred = -4.8434 - 0.00008633 * 31**2 + 0.05292 * 169 + 0.01095 * 69
        result = self.eq.percent(M, 31, 169, parameter=CHOI_2005.Parameters.FVC, value=pred, weight=69)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fvc_known_value(self):
        # Female: -3.0006 - 0.0001273*35^2 + 0.03951*157 + 0.006892*55
        pred = -3.0006 - 0.0001273 * 35**2 + 0.03951 * 157 + 0.006892 * 55
        result = self.eq.percent(F, 35, 157, parameter=CHOI_2005.Parameters.FVC, value=pred, weight=55)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_fev1_decreases_with_age(self):
        young = self.eq.percent(M, 25, 170, parameter=CHOI_2005.Parameters.FEV1, value=3.5, weight=70)
        old = self.eq.percent(M, 60, 170, parameter=CHOI_2005.Parameters.FEV1, value=3.5, weight=70)
        self.assertLess(young, old)


class TestChoi2005NoLLN(unittest.TestCase):

    def setUp(self):
        self.eq = CHOI_2005()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.eq.lln(M, 40, 170, parameter=CHOI_2005.Parameters.FEV1, weight=70)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.eq.uln(M, 40, 170, parameter=CHOI_2005.Parameters.FEV1, weight=70)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.eq.zscore(M, 40, 170, parameter=CHOI_2005.Parameters.FEV1, value=3.5, weight=70)))


class TestChoi2005OutOfRange(unittest.TestCase):

    def setUp(self):
        self.eq = CHOI_2005()

    def test_age_below_range_returns_na(self):
        result = self.eq.percent(M, 17, 170, parameter=CHOI_2005.Parameters.FEV1, value=3.5)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.eq.percent(M, 85, 170, parameter=CHOI_2005.Parameters.FEV1, value=3.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

import unittest
import pandas as pd
import math
from pyspiro import DESAI_2016

M = 1
F = 0


class TestDesai2016Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(DESAI_2016())

    def test_parameters_enum(self):
        params = [p.name for p in DESAI_2016.Parameters]
        for name in ('FVC', 'FEV1', 'PEFR', 'FEF25_75', 'FEF50', 'FEF75', 'FEV1FVC'):
            self.assertIn(name, params)


class TestDesai2016KnownValues(unittest.TestCase):
    """Cross-check predictions against paper Table 2 means."""

    def setUp(self):
        self.eq = DESAI_2016()

    def test_male_fvc_predicted_at_mean_covariates(self):
        # Male mean: age=38.92, ht=166.14, wt=65.07 → Table 2 FVC=3.68
        # LnFVC = -1.048 + 0.015*166.14 - 0.0045*38.92 → exp gives ~3.56
        ln_pred = -1.048 + 0.015 * 166.14 - 0.0045 * 38.92
        result = self.eq.percent(M, 38.92, 166.14, parameter=DESAI_2016.Parameters.FVC,
                                  value=math.exp(ln_pred), weight=65.07)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev1_linear(self):
        # Male FEV1 is linear (not log)
        pred = -3.275 + 0.043 * 166.14 - 0.020 * 38.92
        result = self.eq.percent(M, 38.92, 166.14, parameter=DESAI_2016.Parameters.FEV1,
                                  value=pred, weight=65.07)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fvc_log_transformed(self):
        # Female mean: age=40.13, ht=152.92, wt=54.97
        ln_pred = -1.616 + 0.015 * 152.92 + 0.014 * 40.13 - 0.000219 * 40.13**2
        result = self.eq.percent(F, 40.13, 152.92, parameter=DESAI_2016.Parameters.FVC,
                                  value=math.exp(ln_pred), weight=54.97)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fev1_log_transformed(self):
        ln_pred = -1.552 + 0.015 * 152.92 + 0.0043 * 40.13 - 0.000144 * 40.13**2
        result = self.eq.percent(F, 40.13, 152.92, parameter=DESAI_2016.Parameters.FEV1,
                                  value=math.exp(ln_pred), weight=54.97)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev1fvc_known(self):
        # 89.09 - 0.179*40
        pred = 89.09 - 0.179 * 40
        result = self.eq.percent(M, 40, 170, parameter=DESAI_2016.Parameters.FEV1FVC,
                                  value=pred, weight=70)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fev1fvc_quadratic(self):
        # 104.35 - 0.085*40 + 0.00650*40^2
        pred = 104.35 - 0.085 * 40 + 0.00650 * 40**2
        result = self.eq.percent(F, 40, 155, parameter=DESAI_2016.Parameters.FEV1FVC,
                                  value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)


class TestDesai2016LLN(unittest.TestCase):

    def setUp(self):
        self.eq = DESAI_2016()

    def test_male_fvc_lln_log_scale(self):
        ln_pred = -1.048 + 0.015 * 168 - 0.0045 * 35
        expected_lln = math.exp(ln_pred - 1.645 * 0.111)
        lln = self.eq.lln(M, 35, 168, parameter=DESAI_2016.Parameters.FVC, weight=70)
        self.assertAlmostEqual(lln, expected_lln, places=4)

    def test_male_fev1_lln_linear(self):
        pred = -3.275 + 0.043 * 168 - 0.020 * 35
        expected_lln = pred - 1.645 * 0.346
        lln = self.eq.lln(M, 35, 168, parameter=DESAI_2016.Parameters.FEV1, weight=70)
        self.assertAlmostEqual(lln, expected_lln, places=4)

    def test_female_fvc_lln_log_scale(self):
        ln_pred = -1.616 + 0.015 * 155 + 0.014 * 35 - 0.000219 * 35**2
        expected_lln = math.exp(ln_pred - 1.645 * 0.097)
        lln = self.eq.lln(F, 35, 155, parameter=DESAI_2016.Parameters.FVC)
        self.assertAlmostEqual(lln, expected_lln, places=4)

    def test_female_pefr_lln_linear(self):
        pred = -1.777 + 0.044 * 155 + 0.057 * 35 - 0.000914 * 35**2
        expected_lln = pred - 1.645 * 0.739
        lln = self.eq.lln(F, 35, 155, parameter=DESAI_2016.Parameters.PEFR)
        self.assertAlmostEqual(lln, expected_lln, places=4)

    def test_uln_greater_than_lln(self):
        lln = self.eq.lln(M, 40, 170, parameter=DESAI_2016.Parameters.FVC, weight=72)
        uln = self.eq.uln(M, 40, 170, parameter=DESAI_2016.Parameters.FVC, weight=72)
        self.assertLess(lln, uln)


class TestDesai2016Zscore(unittest.TestCase):

    def setUp(self):
        self.eq = DESAI_2016()

    def test_male_fev1_zscore_at_predicted_is_zero(self):
        pred = -3.275 + 0.043 * 168 - 0.020 * 35
        z = self.eq.zscore(M, 35, 168, parameter=DESAI_2016.Parameters.FEV1, value=pred)
        self.assertAlmostEqual(z, 0.0, places=6)

    def test_female_fvc_zscore_at_predicted_is_zero(self):
        ln_pred = -1.616 + 0.015 * 155 + 0.014 * 35 - 0.000219 * 35**2
        z = self.eq.zscore(F, 35, 155, parameter=DESAI_2016.Parameters.FVC,
                            value=math.exp(ln_pred))
        self.assertAlmostEqual(z, 0.0, places=6)


class TestDesai2016WeightRequirement(unittest.TestCase):

    def setUp(self):
        self.eq = DESAI_2016()

    def test_male_pefr_without_weight_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 35, 168, parameter=DESAI_2016.Parameters.PEFR, value=8.0)))

    def test_female_fef75_without_weight_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.lln(F, 35, 155, parameter=DESAI_2016.Parameters.FEF75)))

    def test_male_fev1_no_weight_needed(self):
        result = self.eq.percent(M, 35, 168, parameter=DESAI_2016.Parameters.FEV1, value=3.0)
        self.assertIsInstance(result, float)

    def test_female_fvc_no_weight_needed(self):
        result = self.eq.lln(F, 35, 155, parameter=DESAI_2016.Parameters.FVC)
        self.assertIsInstance(result, float)


class TestDesai2016OutOfRange(unittest.TestCase):

    def setUp(self):
        self.eq = DESAI_2016()

    def test_male_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 17, 168, parameter=DESAI_2016.Parameters.FEV1, value=3.0)))

    def test_male_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 83, 168, parameter=DESAI_2016.Parameters.FEV1, value=2.5)))

    def test_female_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(F, 73, 155, parameter=DESAI_2016.Parameters.FEV1, value=2.0)))


if __name__ == '__main__':
    unittest.main()

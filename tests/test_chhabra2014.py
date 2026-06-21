import unittest
import pandas as pd
import math
from pyspiro import CHHABRA_2014

M = 1
F = 0


class TestChhabra2014Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(CHHABRA_2014())

    def test_parameters_enum(self):
        params = [p.name for p in CHHABRA_2014.Parameters]
        for name in ('FVC', 'FEV1', 'PEFR', 'FEF25_75', 'FEF50', 'FEF75', 'FEV1FVC'):
            self.assertIn(name, params)


class TestChhabra2014KnownValues(unittest.TestCase):
    """Cross-check predictions against paper Table 3 means."""

    def setUp(self):
        self.eq = CHHABRA_2014()

    def test_male_fvc_near_paper_mean(self):
        # Paper Table 3 training males: age=31.23, ht=169.03, wt=68.73 → mean FVC=4.07
        # Predicted: -5.048 - 0.014*31.23 + 0.054*169.03 + 0.006*68.73 ≈ 4.054
        pred_fvc = -5.048 - 0.014 * 31.23 + 0.054 * 169.03 + 0.006 * 68.73
        result = self.eq.percent(M, 31.23, 169.03, parameter=CHHABRA_2014.Parameters.FVC,
                                  value=pred_fvc, weight=68.73)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_pefr_near_paper_mean(self):
        # Training males: LnPEFR = 0.346 - 0.004*31.23 + 0.011*169.03 → exp gives ~8.01 L/s
        ln_pefr = 0.346 - 0.004 * 31.23 + 0.011 * 169.03
        predicted_pefr = math.exp(ln_pefr)
        self.assertAlmostEqual(predicted_pefr, 8.01, delta=0.1)
        result = self.eq.percent(M, 31.23, 169.03, parameter=CHHABRA_2014.Parameters.PEFR,
                                  value=predicted_pefr, weight=68.73)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev1_near_paper_mean(self):
        # Training males FEV1 mean = 3.29; predicted at mean covariates ≈ 3.34
        pred = -3.682 - 0.024 * 31.23 + 0.046 * 169.03
        result = self.eq.percent(M, 31.23, 169.03, parameter=CHHABRA_2014.Parameters.FEV1,
                                  value=pred, weight=68.73)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fev1fvc_known(self):
        # Female FEV1FVC = 97.182 - 0.440*35
        pred = 97.182 - 0.440 * 35
        result = self.eq.percent(F, 35, 158, parameter=CHHABRA_2014.Parameters.FEV1FVC,
                                  value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)


class TestChhabra2014LLN(unittest.TestCase):

    def setUp(self):
        self.eq = CHHABRA_2014()

    def test_male_fvc_lln_below_predicted(self):
        lln = self.eq.lln(M, 35, 169, parameter=CHHABRA_2014.Parameters.FVC, weight=70)
        pred = self.eq.percent(M, 35, 169, parameter=CHHABRA_2014.Parameters.FVC,
                                value=5.0, weight=70)
        predicted_val = 5.0 / pred * 100 if not pd.isna(pred) else None
        self.assertIsInstance(lln, float)
        # LLN = pred - 1.645*0.479; verify it's less than predicted
        fvc_pred = -5.048 - 0.014 * 35 + 0.054 * 169 + 0.006 * 70
        self.assertAlmostEqual(lln, fvc_pred - 1.645 * 0.479, places=4)

    def test_male_pefr_lln_log_scale(self):
        # PEFR is log-transformed: LLN = exp(ln_pred - 1.645*0.158)
        ln_pred = 0.346 - 0.004 * 35 + 0.011 * 169
        expected_lln = math.exp(ln_pred - 1.645 * 0.158)
        lln = self.eq.lln(M, 35, 169, parameter=CHHABRA_2014.Parameters.PEFR)
        self.assertAlmostEqual(lln, expected_lln, places=4)

    def test_male_pefr_uln_log_scale(self):
        ln_pred = 0.346 - 0.004 * 35 + 0.011 * 169
        expected_uln = math.exp(ln_pred + 1.645 * 0.158)
        uln = self.eq.uln(M, 35, 169, parameter=CHHABRA_2014.Parameters.PEFR)
        self.assertAlmostEqual(uln, expected_uln, places=4)

    def test_female_fvc_lln_linear(self):
        pred = 20.07 - 0.010 * 35 - 0.261 * 158 + 0.000972 * 158**2
        expected_lln = pred - 1.645 * 0.315
        lln = self.eq.lln(F, 35, 158, parameter=CHHABRA_2014.Parameters.FVC)
        self.assertAlmostEqual(lln, expected_lln, places=4)

    def test_lln_less_than_predicted(self):
        lln = self.eq.lln(M, 40, 170, parameter=CHHABRA_2014.Parameters.FEV1)
        pred_val = -3.682 - 0.024 * 40 + 0.046 * 170
        self.assertLess(lln, pred_val)

    def test_uln_greater_than_predicted(self):
        uln = self.eq.uln(F, 40, 160, parameter=CHHABRA_2014.Parameters.FEV1)
        pred_val = -2.267 - 0.019 * 40 + 0.033 * 160
        self.assertGreater(uln, pred_val)


class TestChhabra2014Zscore(unittest.TestCase):

    def setUp(self):
        self.eq = CHHABRA_2014()

    def test_male_fev1_zscore_at_predicted_is_zero(self):
        pred = -3.682 - 0.024 * 35 + 0.046 * 169
        z = self.eq.zscore(M, 35, 169, parameter=CHHABRA_2014.Parameters.FEV1, value=pred)
        self.assertAlmostEqual(z, 0.0, places=6)

    def test_male_pefr_zscore_at_predicted_is_zero(self):
        ln_pred = 0.346 - 0.004 * 35 + 0.011 * 169
        z = self.eq.zscore(M, 35, 169, parameter=CHHABRA_2014.Parameters.PEFR,
                            value=math.exp(ln_pred))
        self.assertAlmostEqual(z, 0.0, places=6)


class TestChhabra2014WeightRequirement(unittest.TestCase):

    def setUp(self):
        self.eq = CHHABRA_2014()

    def test_male_fvc_without_weight_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 35, 169, parameter=CHHABRA_2014.Parameters.FVC, value=4.0)))

    def test_male_fef75_without_weight_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.lln(M, 35, 169, parameter=CHHABRA_2014.Parameters.FEF75)))

    def test_male_fev1fvc_without_weight_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 35, 169, parameter=CHHABRA_2014.Parameters.FEV1FVC, value=80)))

    def test_female_no_weight_needed_for_fev1(self):
        result = self.eq.percent(F, 35, 158, parameter=CHHABRA_2014.Parameters.FEV1, value=2.5)
        self.assertIsInstance(result, float)


class TestChhabra2014OutOfRange(unittest.TestCase):

    def setUp(self):
        self.eq = CHHABRA_2014()

    def test_male_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 17, 169, parameter=CHHABRA_2014.Parameters.FEV1, value=3.0)))

    def test_male_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 72, 169, parameter=CHHABRA_2014.Parameters.FEV1, value=2.5)))

    def test_female_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(F, 66, 158, parameter=CHHABRA_2014.Parameters.FEV1, value=2.0)))


if __name__ == '__main__':
    unittest.main()

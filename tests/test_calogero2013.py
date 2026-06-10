"""
Tests for CALOGERO_2013 (pediatric oscillometry reference equations).

All expected values are pre-computed from Table 2 of Calogero et al. 2013
(Pediatr Pulmonol 2013;48:707-715) using the regression equations and
back-transformations described in the paper.

Transformation summary:
    Rrs6/8/10 : ln(Rrs) = a + b_sex × sex + b_ht × height
    Xrs6/8/10 : √(10 − Xrs) = a + b_sex × sex + b_ht × height
    AX        : √AX = a + b_sex × sex + b_ht × height
    Fres      : Fres = a + b_ht × height  (no sex term)

Z-score: z = (T_measured − T_predicted) / SEE  (all on transformed scale)
LLN/ULN: 5th/95th percentile on the clinical scale (T ± 1.645 × SEE back-transformed).
"""

import math
import sys
import unittest

import pandas

sys.path.insert(0, '/media/veracrypt1/Projekte/PySpiro')
from pyspiro.src.oscillometry.CALOGERO_2013 import CALOGERO_2013


class TestCOEFFICIENTS(unittest.TestCase):
    """Verify coefficient storage via predicted values."""

    def setUp(self):
        self.c = CALOGERO_2013()
        self.P = CALOGERO_2013.Parameters

    def test_predicted_rrs6_female_h120(self):
        # T = 3.37377 - 0.04157×0 - 0.01155×120 = 1.98777 → exp = 7.2992
        val = self.c.predicted(0, 8.0, 120.0, self.P.Rrs6.value)
        self.assertAlmostEqual(val, 7.2992, delta=0.001)

    def test_predicted_rrs8_female_h120(self):
        val = self.c.predicted(0, 8.0, 120.0, self.P.Rrs8.value)
        self.assertAlmostEqual(val, 7.1751, delta=0.001)

    def test_predicted_rrs10_female_h120(self):
        val = self.c.predicted(0, 8.0, 120.0, self.P.Rrs10.value)
        self.assertAlmostEqual(val, 6.7615, delta=0.001)

    def test_predicted_xrs6_female_h120(self):
        # T = 4.23244 - 0.00537×120 = 3.58804 → 10 - 3.58804² = -2.874
        val = self.c.predicted(0, 8.0, 120.0, self.P.Xrs6.value)
        self.assertAlmostEqual(val, -2.8740, delta=0.001)

    def test_predicted_xrs8_female_h120(self):
        val = self.c.predicted(0, 8.0, 120.0, self.P.Xrs8.value)
        self.assertAlmostEqual(val, -2.3331, delta=0.001)

    def test_predicted_xrs10_female_h120(self):
        val = self.c.predicted(0, 8.0, 120.0, self.P.Xrs10.value)
        self.assertAlmostEqual(val, -2.1991, delta=0.001)

    def test_predicted_ax_female_h120(self):
        # T = 11.90851 - 0.05518×120 = 5.28691 → 5.28691² = 27.951
        val = self.c.predicted(0, 8.0, 120.0, self.P.AX.value)
        self.assertAlmostEqual(val, 27.951, delta=0.01)

    def test_predicted_fres_female_h120(self):
        # T = 45.68724 - 0.17763×120 = 24.372
        val = self.c.predicted(0, 8.0, 120.0, self.P.Fres.value)
        self.assertAlmostEqual(val, 24.372, delta=0.01)

    def test_predicted_rrs6_male_h140(self):
        # T = 3.37377 - 0.04157×1 - 0.01155×140 = 1.71420 → exp = 5.5578
        val = self.c.predicted(1, 10.0, 140.0, self.P.Rrs6.value)
        self.assertAlmostEqual(val, 5.5578, delta=0.001)

    def test_predicted_fres_male_h140(self):
        # Fres has no sex term: 45.68724 - 0.17763×140 = 20.819
        val = self.c.predicted(1, 10.0, 140.0, self.P.Fres.value)
        self.assertAlmostEqual(val, 20.819, delta=0.01)


class TestSexEffects(unittest.TestCase):

    def setUp(self):
        self.c = CALOGERO_2013()
        self.P = CALOGERO_2013.Parameters

    def test_rrs_males_lower_than_females(self):
        """Boys have wider airways for same height → lower Rrs."""
        pred_f = self.c.predicted(0, 8.0, 130.0, self.P.Rrs6.value)
        pred_m = self.c.predicted(1, 8.0, 130.0, self.P.Rrs6.value)
        self.assertGreater(pred_f, pred_m)

    def test_xrs_males_less_negative_than_females(self):
        pred_f = self.c.predicted(0, 8.0, 130.0, self.P.Xrs6.value)
        pred_m = self.c.predicted(1, 8.0, 130.0, self.P.Xrs6.value)
        self.assertLess(pred_f, pred_m)  # female Xrs is more negative

    def test_ax_males_lower_than_females(self):
        pred_f = self.c.predicted(0, 8.0, 130.0, self.P.AX.value)
        pred_m = self.c.predicted(1, 8.0, 130.0, self.P.AX.value)
        self.assertGreater(pred_f, pred_m)

    def test_fres_no_sex_effect(self):
        """Fres has no significant sex term."""
        pred_f = self.c.predicted(0, 8.0, 130.0, self.P.Fres.value)
        pred_m = self.c.predicted(1, 8.0, 130.0, self.P.Fres.value)
        self.assertAlmostEqual(pred_f, pred_m, places=8)


class TestHeightEffects(unittest.TestCase):

    def setUp(self):
        self.c = CALOGERO_2013()
        self.P = CALOGERO_2013.Parameters

    def test_rrs_decreases_with_height(self):
        pred_tall   = self.c.predicted(0, 12.0, 155.0, self.P.Rrs6.value)
        pred_short  = self.c.predicted(0, 5.0,  100.0, self.P.Rrs6.value)
        self.assertLess(pred_tall, pred_short)

    def test_xrs_less_negative_with_height(self):
        """Taller children have less negative Xrs (larger airways)."""
        pred_tall  = self.c.predicted(0, 12.0, 155.0, self.P.Xrs6.value)
        pred_short = self.c.predicted(0, 5.0,  100.0, self.P.Xrs6.value)
        self.assertGreater(pred_tall, pred_short)

    def test_fres_decreases_with_height(self):
        pred_tall  = self.c.predicted(0, 12.0, 155.0, self.P.Fres.value)
        pred_short = self.c.predicted(0, 5.0,  100.0, self.P.Fres.value)
        self.assertLess(pred_tall, pred_short)

    def test_ax_decreases_with_height(self):
        pred_tall  = self.c.predicted(0, 12.0, 155.0, self.P.AX.value)
        pred_short = self.c.predicted(0, 5.0,  100.0, self.P.AX.value)
        self.assertLess(pred_tall, pred_short)


class TestZscore(unittest.TestCase):

    def setUp(self):
        self.c = CALOGERO_2013()
        self.P = CALOGERO_2013.Parameters

    def test_zscore_rrs6_at_predicted_is_zero(self):
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Rrs6.value)
        z = self.c.zscore(0, 8.0, 120.0, self.P.Rrs6.value, pred)
        self.assertAlmostEqual(z, 0.0, places=3)

    def test_zscore_xrs6_at_predicted_is_zero(self):
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Xrs6.value)
        z = self.c.zscore(0, 8.0, 120.0, self.P.Xrs6.value, pred)
        self.assertAlmostEqual(z, 0.0, places=3)

    def test_zscore_ax_at_predicted_is_zero(self):
        pred = self.c.predicted(0, 8.0, 120.0, self.P.AX.value)
        z = self.c.zscore(0, 8.0, 120.0, self.P.AX.value, pred)
        self.assertAlmostEqual(z, 0.0, places=3)

    def test_zscore_fres_at_predicted_is_zero(self):
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Fres.value)
        z = self.c.zscore(0, 8.0, 120.0, self.P.Fres.value, pred)
        self.assertAlmostEqual(z, 0.0, places=3)

    def test_zscore_rrs6_value_8_0_female_h120(self):
        # T_meas = ln(8.0) = 2.07944, T_pred = 1.98777, SEE=0.223
        # z = (2.07944 - 1.98777) / 0.223 = 0.411
        z = self.c.zscore(0, 8.0, 120.0, self.P.Rrs6.value, 8.0)
        self.assertAlmostEqual(z, 0.4111, delta=0.001)

    def test_zscore_xrs6_value_neg5_female_h120(self):
        # T_meas = sqrt(10 - (-5)) = sqrt(15) = 3.87298
        # T_pred = 3.58804, SEE = 0.137
        # z = (3.87298 - 3.58804) / 0.137 = 2.0799
        z = self.c.zscore(0, 8.0, 120.0, self.P.Xrs6.value, -5.0)
        self.assertAlmostEqual(z, 2.0799, delta=0.001)

    def test_zscore_rrs6_high_value_positive(self):
        """Elevated Rrs gives positive z (worse than predicted)."""
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Rrs6.value)
        z = self.c.zscore(0, 8.0, 120.0, self.P.Rrs6.value, pred * 1.5)
        self.assertGreater(z, 0)

    def test_zscore_xrs6_more_negative_positive(self):
        """More negative Xrs than predicted gives positive z (worse)."""
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Xrs6.value)
        z = self.c.zscore(0, 8.0, 120.0, self.P.Xrs6.value, pred - 2.0)
        self.assertGreater(z, 0)

    def test_zscore_at_uln_is_plus_1645(self):
        """ULN corresponds to z = +1.645 for Rrs (higher end)."""
        uln = self.c.uln(0, 8.0, 130.0, self.P.Rrs6.value)
        z = self.c.zscore(0, 8.0, 130.0, self.P.Rrs6.value, uln)
        self.assertAlmostEqual(z, 1.645, delta=0.01)

    def test_zscore_at_lln_is_neg_1645_for_rrs(self):
        lln = self.c.lln(0, 8.0, 130.0, self.P.Rrs6.value)
        z = self.c.zscore(0, 8.0, 130.0, self.P.Rrs6.value, lln)
        self.assertAlmostEqual(z, -1.645, delta=0.01)

    def test_zscore_at_xrs_lln_is_plus_1645(self):
        """LLN for Xrs (most negative) corresponds to z = +1.645."""
        lln = self.c.lln(0, 8.0, 130.0, self.P.Xrs6.value)
        z = self.c.zscore(0, 8.0, 130.0, self.P.Xrs6.value, lln)
        self.assertAlmostEqual(z, 1.645, delta=0.01)

    def test_zscore_at_xrs_uln_is_neg_1645(self):
        """ULN for Xrs (least negative) corresponds to z = -1.645."""
        uln = self.c.uln(0, 8.0, 130.0, self.P.Xrs6.value)
        z = self.c.zscore(0, 8.0, 130.0, self.P.Xrs6.value, uln)
        self.assertAlmostEqual(z, -1.645, delta=0.01)


class TestLLNandULN(unittest.TestCase):

    def setUp(self):
        self.c = CALOGERO_2013()
        self.P = CALOGERO_2013.Parameters

    # --- Rrs: lln < predicted < uln ----------------------------------------

    def test_rrs6_lln_below_predicted_female_h120(self):
        lln  = self.c.lln(0, 8.0, 120.0, self.P.Rrs6.value)
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Rrs6.value)
        self.assertLess(lln, pred)

    def test_rrs6_uln_above_predicted_female_h120(self):
        uln  = self.c.uln(0, 8.0, 120.0, self.P.Rrs6.value)
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Rrs6.value)
        self.assertGreater(uln, pred)

    def test_rrs6_lln_value_female_h120(self):
        lln = self.c.lln(0, 8.0, 120.0, self.P.Rrs6.value)
        self.assertAlmostEqual(lln, 5.0578, delta=0.001)

    def test_rrs6_uln_value_female_h120(self):
        uln = self.c.uln(0, 8.0, 120.0, self.P.Rrs6.value)
        self.assertAlmostEqual(uln, 10.534, delta=0.001)

    def test_rrs8_lln_female_h120(self):
        lln = self.c.lln(0, 8.0, 120.0, self.P.Rrs8.value)
        self.assertAlmostEqual(lln, 5.0543, delta=0.001)

    def test_rrs8_uln_female_h120(self):
        uln = self.c.uln(0, 8.0, 120.0, self.P.Rrs8.value)
        self.assertAlmostEqual(uln, 10.186, delta=0.001)

    def test_rrs6_lln_male_h140(self):
        lln = self.c.lln(1, 10.0, 140.0, self.P.Rrs6.value)
        self.assertAlmostEqual(lln, 3.8511, delta=0.001)

    def test_rrs6_uln_male_h140(self):
        uln = self.c.uln(1, 10.0, 140.0, self.P.Rrs6.value)
        self.assertAlmostEqual(uln, 8.0208, delta=0.001)

    # --- Xrs: lln < predicted < uln (lln is more negative) -----------------

    def test_xrs6_lln_more_negative_than_predicted(self):
        lln  = self.c.lln(0, 8.0, 120.0, self.P.Xrs6.value)
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Xrs6.value)
        self.assertLess(lln, pred)

    def test_xrs6_uln_less_negative_than_predicted(self):
        uln  = self.c.uln(0, 8.0, 120.0, self.P.Xrs6.value)
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Xrs6.value)
        self.assertGreater(uln, pred)

    def test_xrs6_lln_value_female_h120(self):
        lln = self.c.lln(0, 8.0, 120.0, self.P.Xrs6.value)
        self.assertAlmostEqual(lln, -4.5421, delta=0.001)

    def test_xrs6_uln_value_female_h120(self):
        uln = self.c.uln(0, 8.0, 120.0, self.P.Xrs6.value)
        self.assertAlmostEqual(uln, -1.3076, delta=0.001)

    def test_xrs6_lln_male_h140(self):
        lln = self.c.lln(1, 10.0, 140.0, self.P.Xrs6.value)
        self.assertAlmostEqual(lln, -3.5032, delta=0.001)

    def test_xrs6_uln_male_h140(self):
        uln = self.c.uln(1, 10.0, 140.0, self.P.Xrs6.value)
        self.assertAlmostEqual(uln, -0.3938, delta=0.001)

    # --- AX and Fres --------------------------------------------------------

    def test_ax_lln_female_h120(self):
        lln = self.c.lln(0, 8.0, 120.0, self.P.AX.value)
        self.assertAlmostEqual(lln, 8.592, delta=0.01)

    def test_ax_uln_female_h120(self):
        uln = self.c.uln(0, 8.0, 120.0, self.P.AX.value)
        self.assertAlmostEqual(uln, 58.409, delta=0.01)

    def test_ax_lln_below_predicted(self):
        lln  = self.c.lln(0, 8.0, 120.0, self.P.AX.value)
        pred = self.c.predicted(0, 8.0, 120.0, self.P.AX.value)
        self.assertLess(lln, pred)

    def test_ax_uln_above_predicted(self):
        uln  = self.c.uln(0, 8.0, 120.0, self.P.AX.value)
        pred = self.c.predicted(0, 8.0, 120.0, self.P.AX.value)
        self.assertGreater(uln, pred)

    def test_fres_lln_female_h120(self):
        lln = self.c.lln(0, 8.0, 120.0, self.P.Fres.value)
        self.assertAlmostEqual(lln, 15.905, delta=0.01)

    def test_fres_uln_female_h120(self):
        uln = self.c.uln(0, 8.0, 120.0, self.P.Fres.value)
        self.assertAlmostEqual(uln, 32.839, delta=0.01)

    def test_fres_lln_male_h140(self):
        lln = self.c.lln(1, 10.0, 140.0, self.P.Fres.value)
        self.assertAlmostEqual(lln, 12.352, delta=0.01)

    def test_fres_uln_male_h140(self):
        uln = self.c.uln(1, 10.0, 140.0, self.P.Fres.value)
        self.assertAlmostEqual(uln, 29.286, delta=0.01)


class TestPercent(unittest.TestCase):

    def setUp(self):
        self.c = CALOGERO_2013()
        self.P = CALOGERO_2013.Parameters

    def test_percent_rrs6_at_predicted_is_100(self):
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Rrs6.value)
        pct = self.c.percent(0, 8.0, 120.0, self.P.Rrs6.value, pred)
        self.assertAlmostEqual(pct, 100.0, delta=0.01)

    def test_percent_rrs6_value_8_0_female_h120(self):
        # predicted = 7.2992, 8.0/7.2992 * 100 = 109.60
        pct = self.c.percent(0, 8.0, 120.0, self.P.Rrs6.value, 8.0)
        self.assertAlmostEqual(pct, 109.60, delta=0.05)

    def test_percent_ax_at_predicted_is_100(self):
        pred = self.c.predicted(0, 8.0, 120.0, self.P.AX.value)
        pct = self.c.percent(0, 8.0, 120.0, self.P.AX.value, pred)
        self.assertAlmostEqual(pct, 100.0, delta=0.01)

    def test_percent_fres_at_predicted_is_100(self):
        pred = self.c.predicted(0, 8.0, 120.0, self.P.Fres.value)
        pct = self.c.percent(0, 8.0, 120.0, self.P.Fres.value, pred)
        self.assertAlmostEqual(pct, 100.0, delta=0.01)

    def test_percent_xrs_returns_na(self):
        """percent() is not defined for signed Xrs parameters."""
        for p in [self.P.Xrs6, self.P.Xrs8, self.P.Xrs10]:
            result = self.c.percent(0, 8.0, 120.0, p.value, -3.0)
            self.assertTrue(pandas.isna(result), msg=f"Expected NA for {p.name}")


class TestHeightRange(unittest.TestCase):

    def setUp(self):
        self.c = CALOGERO_2013()
        self.P = CALOGERO_2013.Parameters

    def test_height_92_valid(self):
        result = self.c.predicted(0, 3.0, 92.0, self.P.Rrs6.value)
        self.assertFalse(pandas.isna(result))
        self.assertGreater(result, 0)

    def test_height_159_valid(self):
        result = self.c.predicted(0, 13.0, 159.0, self.P.Rrs6.value)
        self.assertFalse(pandas.isna(result))
        self.assertGreater(result, 0)

    def test_height_below_range_returns_na(self):
        self.c.set_strategy('ignore')
        result = self.c.predicted(0, 2.0, 80.0, self.P.Rrs6.value)
        self.assertTrue(pandas.isna(result))

    def test_height_above_range_returns_na(self):
        self.c.set_strategy('ignore')
        result = self.c.predicted(0, 14.0, 170.0, self.P.Rrs6.value)
        self.assertTrue(pandas.isna(result))

    def test_strategy_closest_clamps(self):
        self.c.set_strategy('closest')
        result_clamped = self.c.predicted(0, 2.0, 80.0, self.P.Rrs6.value)
        self.c.set_strategy('ignore')
        result_boundary = self.c.predicted(0, 2.0, 92.0, self.P.Rrs6.value)
        self.assertAlmostEqual(float(result_clamped), float(result_boundary), places=4)

    def test_lms_returns_na(self):
        L, M, S = self.c.lms(0, 8.0, 120.0, self.P.Rrs6.value)
        self.assertTrue(pandas.isna(L))
        self.assertTrue(pandas.isna(M))
        self.assertTrue(pandas.isna(S))


class TestComputeDataFrame(unittest.TestCase):

    def setUp(self):
        import pandas as pd
        self.df = pd.DataFrame({
            'sex':    [0, 1, 0],
            'age':    [6.0, 10.0, 8.0],
            'height': [112.0, 138.0, 125.0],
            'Rrs6':   [7.5, 5.2, 6.8],
            'Xrs6':   [-3.1, -1.8, -2.5],
        })

    def test_compute_zscore_rrs6(self):
        c = CALOGERO_2013()
        result = c.compute(self.df, CALOGERO_2013.Parameters.Rrs6,
                           value_col='Rrs6', metrics=('zscore',))
        self.assertEqual(len(result), 3)
        self.assertFalse(result['zscore'].isna().any())

    def test_compute_lln_uln_xrs6(self):
        c = CALOGERO_2013()
        result = c.compute(self.df, CALOGERO_2013.Parameters.Xrs6,
                           metrics=('lln', 'uln'))
        self.assertEqual(len(result), 3)
        # LLN must be less than ULN for Xrs (lln is more negative)
        for i in range(3):
            self.assertLess(result['lln'].iloc[i], result['uln'].iloc[i])

    def test_compute_percent_rrs_not_na(self):
        c = CALOGERO_2013()
        result = c.compute(self.df, CALOGERO_2013.Parameters.Rrs6,
                           value_col='Rrs6', metrics=('percent',))
        self.assertFalse(result['percent'].isna().any())

    def test_compute_percent_xrs_all_na(self):
        c = CALOGERO_2013()
        result = c.compute(self.df, CALOGERO_2013.Parameters.Xrs6,
                           value_col='Xrs6', metrics=('percent',))
        self.assertTrue(result['percent'].isna().all())

    def test_compute_all_parameters_produce_values(self):
        import pandas as pd
        c = CALOGERO_2013()
        df = pd.DataFrame({
            'sex':    [0], 'age': [7.0], 'height': [120.0],
            'val':    [5.0],
        })
        for p in CALOGERO_2013.Parameters:
            if p in [CALOGERO_2013.Parameters.Xrs6, CALOGERO_2013.Parameters.Xrs8,
                     CALOGERO_2013.Parameters.Xrs10]:
                continue  # percent NA for Xrs; tested separately
            result = c.compute(df, p, value_col='val', metrics=('lln', 'uln'))
            self.assertFalse(result['lln'].isna().any(), msg=f"lln NA for {p}")
            self.assertFalse(result['uln'].isna().any(), msg=f"uln NA for {p}")


if __name__ == '__main__':
    unittest.main()

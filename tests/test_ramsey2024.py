"""
Tests for RAMSEY_2024 (GLI MBW reference equations).

All expected values are pre-computed from the GAMLSS BCCG equations published
in Ramsey et al. 2024, Table 2, combined with age-spline lookup tables from
supplementary material 3.  ULN values at ages 5 and 20 are cross-checked
against Table 3 of the same paper.
"""

import math
import sys
import unittest

import pandas

sys.path.insert(0, '/media/veracrypt1/Projekte/PySpiro')
from pyspiro.src.mbw.RAMSEY_2024 import RAMSEY_2024


class TestRAMSEY2024_LCI(unittest.TestCase):

    def setUp(self):
        self.r = RAMSEY_2024()
        self.LCI = RAMSEY_2024.Parameters.LCI

    # ---- lms() ---------------------------------------------------------------

    def test_lci_L_is_fixed(self):
        """L is a fixed constant, not age-dependent."""
        L, _, _ = self.r.lms(0, 10.0, 160.0, self.LCI.value)
        self.assertAlmostEqual(L, -0.3964, places=4)

    def test_lci_lms_age5(self):
        L, M, S = self.r.lms(0, 5.0, 120.0, self.LCI.value)
        self.assertAlmostEqual(L, -0.3964, places=4)
        self.assertAlmostEqual(M, 6.3966, places=3)
        self.assertAlmostEqual(S, 0.09560, places=4)

    def test_lci_lms_age10(self):
        L, M, S = self.r.lms(0, 10.0, 140.0, self.LCI.value)
        self.assertAlmostEqual(M, 6.2789, places=3)
        self.assertAlmostEqual(S, 0.07738, places=4)

    def test_lci_lms_age20(self):
        _, M, S = self.r.lms(1, 20.0, 175.0, self.LCI.value)
        self.assertAlmostEqual(M, 6.1432, places=3)
        self.assertAlmostEqual(S, 0.06453, places=4)

    def test_lci_no_sex_effect(self):
        """LCI has no sex dependence — M must be identical for male and female."""
        _, M_male,   _ = self.r.lms(1, 40.0, 180.0, self.LCI.value)
        _, M_female, _ = self.r.lms(0, 40.0, 160.0, self.LCI.value)
        self.assertAlmostEqual(M_male, M_female, places=8)

    def test_lci_no_height_effect(self):
        """LCI has no height dependence."""
        _, M_a, _ = self.r.lms(1, 30.0, 150.0, self.LCI.value)
        _, M_b, _ = self.r.lms(1, 30.0, 200.0, self.LCI.value)
        self.assertAlmostEqual(M_a, M_b, places=8)

    # ---- ULN cross-checks against Table 3 ------------------------------------

    def test_lci_uln_age5_matches_table3(self):
        """ULN at age 5 should be ≈7.5 (Ramsey 2024 Table 3)."""
        uln = self.r.uln(0, 5.0, 120.0, self.LCI.value)
        self.assertAlmostEqual(uln, 7.52, delta=0.05)

    def test_lci_uln_age20_matches_table3(self):
        """ULN at age 20 should be ≈6.9 (Ramsey 2024 Table 3)."""
        uln = self.r.uln(0, 20.0, 170.0, self.LCI.value)
        self.assertAlmostEqual(uln, 6.85, delta=0.05)

    # ---- Derived metrics -----------------------------------------------------

    def test_lci_zscore_age10(self):
        z = self.r.zscore(0, 10.0, 0, self.LCI.value, 8.0)
        self.assertAlmostEqual(z, 2.985, delta=0.002)

    def test_lci_percent_age10(self):
        pct = self.r.percent(0, 10.0, 0, self.LCI.value, 8.0)
        self.assertAlmostEqual(pct, 127.41, delta=0.05)

    def test_lci_lln_age5(self):
        lln = self.r.lln(0, 5.0, 120.0, self.LCI.value)
        self.assertAlmostEqual(lln, 5.4916, delta=0.005)

    def test_lci_lln_age20(self):
        lln = self.r.lln(0, 20.0, 170.0, self.LCI.value)
        self.assertAlmostEqual(lln, 5.5365, delta=0.005)

    def test_lci_uln_above_median(self):
        """ULN must be strictly above median for all tested ages."""
        for age in [5.0, 10.0, 20.0, 40.0, 60.0]:
            _, M, _ = self.r.lms(0, age, 0, self.LCI.value)
            uln = self.r.uln(0, age, 0, self.LCI.value)
            self.assertGreater(uln, M, msg=f'ULN < M at age {age}')

    def test_lci_lln_below_median(self):
        for age in [5.0, 10.0, 20.0, 40.0]:
            _, M, _ = self.r.lms(0, age, 0, self.LCI.value)
            lln = self.r.lln(0, age, 0, self.LCI.value)
            self.assertLess(lln, M, msg=f'LLN > M at age {age}')

    def test_lci_zscore_at_median_is_zero(self):
        _, M, _ = self.r.lms(0, 30.0, 0, self.LCI.value)
        z = self.r.zscore(0, 30.0, 0, self.LCI.value, M)
        self.assertAlmostEqual(z, 0.0, places=6)

    def test_lci_zscore_at_uln_is_1645(self):
        uln = self.r.uln(0, 30.0, 0, self.LCI.value)
        z = self.r.zscore(0, 30.0, 0, self.LCI.value, uln)
        self.assertAlmostEqual(z, 1.645, delta=0.005)

    def test_lci_zscore_at_lln_is_neg_1645(self):
        lln = self.r.lln(0, 30.0, 0, self.LCI.value)
        z = self.r.zscore(0, 30.0, 0, self.LCI.value, lln)
        self.assertAlmostEqual(z, -1.645, delta=0.005)

    # ---- Age boundary --------------------------------------------------------

    def test_lci_age_2_valid(self):
        L, M, S = self.r.lms(0, 2.0, 0, self.LCI.value)
        self.assertFalse(pandas.isna(M))
        self.assertGreater(M, 0)

    def test_lci_age_80_valid(self):
        L, M, S = self.r.lms(0, 80.0, 0, self.LCI.value)
        self.assertFalse(pandas.isna(M))
        self.assertGreater(M, 0)

    def test_lci_age_below_range_returns_na(self):
        self.r.set_strategy('ignore')
        L, M, S = self.r.lms(0, 1.0, 0, self.LCI.value)
        self.assertTrue(pandas.isna(M))

    def test_lci_age_above_range_returns_na(self):
        self.r.set_strategy('ignore')
        L, M, S = self.r.lms(0, 81.0, 0, self.LCI.value)
        self.assertTrue(pandas.isna(M))

    def test_lci_strategy_closest_clamps(self):
        self.r.set_strategy('closest')
        L, M_clamped, S = self.r.lms(0, 1.0, 0, self.LCI.value)
        L2, M_at2, S2 = self.r.lms(0, 2.0, 0, self.LCI.value)
        self.r.set_strategy('ignore')
        self.assertAlmostEqual(float(M_clamped), float(M_at2), places=6)

    # ---- Fractional age (spline interpolation) --------------------------------

    def test_lci_fractional_age_interpolated(self):
        """Age 10.5 should give M between M at 10 and 11."""
        _, M10, _ = self.r.lms(0, 10.0, 0, self.LCI.value)
        _, M11, _ = self.r.lms(0, 11.0, 0, self.LCI.value)
        _, M105, _ = self.r.lms(0, 10.5, 0, self.LCI.value)
        self.assertAlmostEqual(M105, (M10 + M11) / 2, delta=0.01)

    # ---- compute() DataFrame interface ----------------------------------------

    def test_lci_compute_returns_dataframe(self):
        import pandas as pd
        df = pd.DataFrame({'sex': [0, 1], 'age': [10.0, 20.0],
                           'height': [140.0, 170.0], 'LCI': [7.0, 6.5]})
        result = RAMSEY_2024().compute(df, RAMSEY_2024.Parameters.LCI,
                                       value_col='LCI', metrics=('zscore', 'lln', 'uln'))
        self.assertEqual(len(result), 2)
        self.assertIn('zscore', result.columns)
        self.assertIn('lln', result.columns)
        self.assertIn('uln', result.columns)

    def test_lci_compute_percent(self):
        import pandas as pd
        df = pd.DataFrame({'sex': [0], 'age': [10.0], 'height': [140.0], 'LCI': [8.0]})
        result = RAMSEY_2024().compute(df, RAMSEY_2024.Parameters.LCI,
                                       value_col='LCI', metrics=('percent',))
        self.assertAlmostEqual(float(result['percent'].iloc[0]), 127.41, delta=0.05)


class TestRAMSEY2024_FRC(unittest.TestCase):

    def setUp(self):
        self.r = RAMSEY_2024()
        self.FRC = RAMSEY_2024.Parameters.FRC

    def test_frc_L_is_fixed(self):
        L, _, _ = self.r.lms(1, 30.0, 175.0, self.FRC.value)
        self.assertAlmostEqual(L, 0.6471, places=4)

    def test_frc_lms_male_30_175(self):
        L, M, S = self.r.lms(1, 30.0, 175.0, self.FRC.value)
        self.assertAlmostEqual(M, 3.3101, places=3)
        self.assertAlmostEqual(S, 0.1882, delta=0.001)

    def test_frc_lms_female_30_165(self):
        _, M, S = self.r.lms(0, 30.0, 165.0, self.FRC.value)
        self.assertAlmostEqual(M, 2.6046, places=3)
        self.assertAlmostEqual(S, 0.1912, delta=0.001)

    def test_frc_sex_effect(self):
        """FRC must differ between male and female at the same age and height."""
        _, M_male, _   = self.r.lms(1, 30.0, 170.0, self.FRC.value)
        _, M_female, _ = self.r.lms(0, 30.0, 170.0, self.FRC.value)
        self.assertGreater(M_male, M_female)

    def test_frc_height_effect(self):
        """Taller subjects should have higher FRC."""
        _, M_tall,  _ = self.r.lms(1, 30.0, 185.0, self.FRC.value)
        _, M_short, _ = self.r.lms(1, 30.0, 155.0, self.FRC.value)
        self.assertGreater(M_tall, M_short)

    def test_frc_uln_above_median(self):
        uln = self.r.uln(1, 30.0, 175.0, self.FRC.value)
        _, M, _ = self.r.lms(1, 30.0, 175.0, self.FRC.value)
        self.assertGreater(uln, M)

    def test_frc_lln_below_median(self):
        lln = self.r.lln(1, 30.0, 175.0, self.FRC.value)
        _, M, _ = self.r.lms(1, 30.0, 175.0, self.FRC.value)
        self.assertLess(lln, M)

    def test_frc_zscore_at_median_is_zero(self):
        _, M, _ = self.r.lms(1, 30.0, 175.0, self.FRC.value)
        z = self.r.zscore(1, 30.0, 175.0, self.FRC.value, M)
        self.assertAlmostEqual(z, 0.0, places=6)

    def test_frc_zscore_at_uln_is_1645(self):
        uln = self.r.uln(1, 30.0, 175.0, self.FRC.value)
        z = self.r.zscore(1, 30.0, 175.0, self.FRC.value, uln)
        self.assertAlmostEqual(z, 1.645, delta=0.005)

    def test_frc_zscore_value_3_5(self):
        z = self.r.zscore(1, 30.0, 175.0, self.FRC.value, 3.5)
        self.assertAlmostEqual(z, 0.3019, delta=0.002)

    def test_frc_percent_value_3_5(self):
        pct = self.r.percent(1, 30.0, 175.0, self.FRC.value, 3.5)
        self.assertAlmostEqual(pct, 105.74, delta=0.05)

    def test_frc_uln_male_30_175(self):
        uln = self.r.uln(1, 30.0, 175.0, self.FRC.value)
        self.assertAlmostEqual(uln, 4.3892, delta=0.01)

    def test_frc_lln_male_30_175(self):
        lln = self.r.lln(1, 30.0, 175.0, self.FRC.value)
        self.assertAlmostEqual(lln, 2.3431, delta=0.01)

    def test_frc_age_below_range_returns_na(self):
        self.r.set_strategy('ignore')
        L, M, S = self.r.lms(1, 1.5, 100.0, self.FRC.value)
        self.assertTrue(pandas.isna(M))

    def test_frc_age_above_range_returns_na(self):
        self.r.set_strategy('ignore')
        L, M, S = self.r.lms(1, 85.0, 170.0, self.FRC.value)
        self.assertTrue(pandas.isna(M))

    def test_frc_compute_dataframe(self):
        import pandas as pd
        df = pd.DataFrame({'sex': [1, 0], 'age': [30.0, 45.0],
                           'height': [175.0, 162.0], 'FRC': [3.5, 2.8]})
        result = RAMSEY_2024().compute(df, RAMSEY_2024.Parameters.FRC,
                                       value_col='FRC', metrics=('zscore', 'lln', 'uln'))
        self.assertEqual(len(result), 2)
        self.assertFalse(result['zscore'].isna().any())


if __name__ == '__main__':
    unittest.main()

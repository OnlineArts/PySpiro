"""
Tests for the LOELOE_2025 (Loeloe et al. 2025) reference module.

The golden values in GOLDEN are hard-coded snapshots of the reference results
produced by the original study's spirometry calculator: its predicted-value (pv)
and lower-limit-of-normal (lln) outputs for every parameter, both sexes. They are
frozen here on purpose so the suite has no dependency on the source workbook. The
four rows at 50/160, 60/150, 38/170 and 69/189 are the calculator's own worked
examples; the remaining rows are sampled across the grid, deliberately including
decimal ages/heights (185.1, 160.7, 142.2, 173.9, ...) that expose floating-point
rounding drift in the lookup key.

Each tuple is (sex, age, height, {param: (pv, lln)}), sex 0=female, 1=male.
In the original data, gender code 1 == female and gender code 2 == male.
"""

import math
import unittest

import pandas as pd

from pyspiro import LOELOE_2025

F, M = 0, 1
P = LOELOE_2025.Parameters

# (sex, age, height, {param: (predicted_value, lln)}) — extracted from the Excel table.
GOLDEN = [
    # --- Excel calculator's own worked examples (cached S5:Z8) ---
    (F, 50, 160, {'FEV1': (2.4925, 2.18761650649161), 'FVC': (2.92333333333333, 2.52940826597286), 'FEV1FVC': (85.4970588235294, 83.9031921708069), 'FEF25_75': (2.93546875, 2.67820647059113)}),
    (M, 60, 150, {'FEV1': (3.17170731707317, 2.68083939795487), 'FVC': (3.86323529411765, 3.23322522342257), 'FEV1FVC': (82.4805970149254, 81.0861966736177), 'FEF25_75': (3.41634408602151, 2.99937712188688)}),
    (F, 38, 170, {'FEV1': (2.88555555555556, 2.58067206204716), 'FVC': (3.47111111111111, 3.07718604375064), 'FEV1FVC': (83.2441176470588, 81.6502509943363), 'FEF25_75': (3.17734375, 2.92008147059113)}),
    (M, 69, 189, {'FEV1': (3.30878048780488, 2.81791256868658), 'FVC': (4.08294117647059, 3.45293110577551), 'FEV1FVC': (81.410447761194, 80.0160474198864), 'FEF25_75': (3.56720430107527, 3.15023733694064)}),
    # --- Grid boundaries / corners ---
    (F, 38, 142, {'FEV1': (2.45777777777778, 2.15289428426939), 'FVC': (2.86555555555556, 2.47163048819508), 'FEV1FVC': (85.85, 84.2561333472775), 'FEF25_75': (2.981875, 2.72461272059113)}),
    (M, 38, 142, {'FEV1': (3.44439024390244, 2.95352232478414), 'FVC': (4.21411764705882, 3.58410757636375), 'FEV1FVC': (82.9761194029851, 81.5817190616774), 'FEF25_75': (3.76236559139785, 3.34539862726322)}),
    (F, 69, 142, {'FEV1': (2.18527777777778, 1.88039428426939), 'FVC': (2.54861111111111, 2.15468604375064), 'FEV1FVC': (85.9352941176471, 84.3414274649245), 'FEF25_75': (2.7646875, 2.50742522059113)}),
    # --- Decimal ages/heights (expose round(x/0.1)*0.1 floating-point drift) ---
    (M, 38, 185.1, {'FEV1': (3.94463414634146, 3.45376622722316), 'FVC': (4.98323529411765, 4.35322522342257), 'FEV1FVC': (81.0522388059701, 79.6578384646625), 'FEF25_75': (4.01161290322581, 3.59464593909118)}),
    (M, 50, 160.7, {'FEV1': (3.20560975609756, 2.71474183697926), 'FVC': (3.76588235294118, 3.1358722822461), 'FEV1FVC': (83.355223880597, 81.9608235392894), 'FEF25_75': (3.57182795698925, 3.15486099285462)}),
    (F, 40, 142.2, {'FEV1': (2.39694444444444, 2.09206095093605), 'FVC': (2.80055555555556, 2.40663048819508), 'FEV1FVC': (85.9323529411765, 84.338486288454), 'FEF25_75': (2.96921875, 2.71195647059113)}),
    (M, 55.3, 173.9, {'FEV1': (3.41317073170732, 2.92230281258902), 'FVC': (4.23676470588235, 3.60675463518727), 'FEV1FVC': (81.544776119403, 80.1503757780954), 'FEF25_75': (3.58806451612903, 3.17109755199441)}),
    (F, 68.9, 158.5, {'FEV1': (2.24194444444444, 1.93706095093605), 'FVC': (2.64972222222222, 2.25579715486175), 'FEV1FVC': (84.8352941176471, 83.2414274649246), 'FEF25_75': (2.7190625, 2.46180022059113)}),
    (M, 44.4, 167.3, {'FEV1': (3.39439024390244, 2.90352232478414), 'FVC': (4.105, 3.47498992930492), 'FEV1FVC': (82.9567164179104, 81.5623160766028), 'FEF25_75': (3.73279569892473, 3.31582873479011)}),
    (F, 52.7, 149.8, {'FEV1': (2.27027777777778, 1.96539428426939), 'FVC': (2.64472222222222, 2.25079715486175), 'FEV1FVC': (86.1529411764706, 84.5590745237481), 'FEF25_75': (2.80046875, 2.54320647059113)}),
    (M, 63.1, 180.2, {'FEV1': (3.34243902439024, 2.85157110527194), 'FVC': (4.08294117647059, 3.45293110577551), 'FEV1FVC': (81.3149253731343, 79.9205250318267), 'FEF25_75': (3.52784946236559, 3.11088249823097)}),
]


class TestIran2025Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(LOELOE_2025())

    def test_parameters_enum(self):
        params = [p.name for p in LOELOE_2025.Parameters]
        for name in ('FEV1', 'FVC', 'FEV1FVC', 'FEF25_75'):
            self.assertIn(name, params)

    def test_lookup_table_loaded(self):
        eq = LOELOE_2025()
        # 311 ages (38.0-69.0) x 471 heights (142.0-189.0) = 146481 grid rows.
        self.assertEqual(len(eq._lookup.index), 146481)


class TestIran2025AgainstExcel(unittest.TestCase):
    """Every golden pv/lln taken from the Excel calculator must be reproduced."""

    def setUp(self):
        self.eq = LOELOE_2025()

    def test_predicted_and_lln_match_excel(self):
        for sex, age, height, params in GOLDEN:
            for pname, (exp_pv, exp_lln) in params.items():
                param = P[pname].value
                pv, lln = self.eq._get_pv_lln(sex, age, height, param)
                with self.subTest(sex=sex, age=age, height=height, param=pname):
                    self.assertFalse(pv is pd.NA, "predicted value unexpectedly NA")
                    self.assertAlmostEqual(float(pv), exp_pv, places=9)
                    self.assertAlmostEqual(float(lln), exp_lln, places=9)

    def test_lln_method_matches_excel(self):
        for sex, age, height, params in GOLDEN:
            for pname, (_, exp_lln) in params.items():
                with self.subTest(sex=sex, age=age, height=height, param=pname):
                    lln = self.eq.lln(sex, age, height, P[pname].value)
                    self.assertAlmostEqual(float(lln), exp_lln, places=9)

    def test_percent_at_predicted_is_100(self):
        for sex, age, height, params in GOLDEN:
            for pname, (exp_pv, _) in params.items():
                with self.subTest(sex=sex, age=age, height=height, param=pname):
                    pct = self.eq.percent(sex, age, height, P[pname].value, exp_pv)
                    self.assertAlmostEqual(float(pct), 100.0, places=6)

    def test_zscore_at_predicted_is_zero(self):
        for sex, age, height, params in GOLDEN:
            for pname, (exp_pv, _) in params.items():
                with self.subTest(sex=sex, age=age, height=height, param=pname):
                    z = self.eq.zscore(sex, age, height, P[pname].value, exp_pv)
                    self.assertAlmostEqual(float(z), 0.0, places=9)

    def test_zscore_at_lln_is_minus_1_645(self):
        # LLN is defined as the 5th percentile == -1.645 SD under the normal approximation.
        for sex, age, height, params in GOLDEN:
            for pname, (_, exp_lln) in params.items():
                with self.subTest(sex=sex, age=age, height=height, param=pname):
                    z = self.eq.zscore(sex, age, height, P[pname].value, exp_lln)
                    self.assertAlmostEqual(float(z), -1.645, places=6)

    def test_uln_mirrors_lln_about_predicted(self):
        for sex, age, height, params in GOLDEN:
            for pname, (exp_pv, exp_lln) in params.items():
                with self.subTest(sex=sex, age=age, height=height, param=pname):
                    uln = self.eq.uln(sex, age, height, P[pname].value)
                    self.assertAlmostEqual(float(uln), 2 * exp_pv - exp_lln, places=9)


class TestIran2025Rounding(unittest.TestCase):
    """The decimal-height regression: every grid point must be retrievable."""

    def setUp(self):
        self.eq = LOELOE_2025()

    def test_all_male_grid_points_resolve(self):
        # Males cover the full grid; passing each stored key back must never miss.
        misses = 0
        for (age, height) in self.eq._lookup.index:
            pv, _ = self.eq._get_pv_lln(M, age, height, P.FEV1.value)
            if pv is pd.NA or (isinstance(pv, float) and math.isnan(pv)):
                misses += 1
        self.assertEqual(misses, 0)

    def test_offgrid_input_rounds_to_nearest_tenth(self):
        # 159.97 -> 160.0, 50.04 -> 50.0 : same value as the on-grid lookup.
        on_grid = self.eq._get_pv_lln(F, 50.0, 160.0, P.FEV1.value)
        off_grid = self.eq._get_pv_lln(F, 50.04, 159.97, P.FEV1.value)
        self.assertAlmostEqual(float(on_grid[0]), float(off_grid[0]), places=12)
        self.assertAlmostEqual(float(on_grid[1]), float(off_grid[1]), places=12)


class TestIran2025OutOfRangeAndMissing(unittest.TestCase):

    def setUp(self):
        self.eq = LOELOE_2025()

    def test_out_of_range_returns_na(self):
        self.assertTrue(self.eq.percent(M, 30, 200, P.FEV1.value, 3.0) is pd.NA)
        self.assertTrue(self.eq.lln(M, 30, 200, P.FEV1.value) is pd.NA)
        self.assertTrue(self.eq.uln(M, 30, 200, P.FEV1.value) is pd.NA)
        pv, lln = self.eq._get_pv_lln(M, 30, 200, P.FEV1.value)
        self.assertTrue(pv is pd.NA and lln is pd.NA)

    def test_missing_female_combo_returns_na(self):
        # (38, 185.1) exists for males but not females; the CSV cell is blank.
        pv, lln = self.eq._get_pv_lln(F, 38, 185.1, P.FEV1.value)
        self.assertTrue(pv is pd.NA and lln is pd.NA)
        self.assertTrue(self.eq.percent(F, 38, 185.1, P.FEV1.value, 3.0) is pd.NA)
        self.assertTrue(self.eq.zscore(F, 38, 185.1, P.FEV1.value, 3.0) is pd.NA)
        self.assertTrue(self.eq.lln(F, 38, 185.1, P.FEV1.value) is pd.NA)
        # ...but males at the same point still resolve.
        pv_m, _ = self.eq._get_pv_lln(M, 38, 185.1, P.FEV1.value)
        self.assertFalse(pv_m is pd.NA)


if __name__ == '__main__':
    unittest.main()

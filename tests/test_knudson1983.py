import unittest
import pandas as pd
from pyspiro import KNUDSON_1983

M = 1
F = 0


class TestKnudson1983Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(KNUDSON_1983())

    def test_age_ranges(self):
        k = KNUDSON_1983()
        self.assertEqual(k._AGE_MALE_RANGE, (6, 90))
        self.assertEqual(k._AGE_FEMALE_RANGE, (6, 88))

    def test_height_ranges(self):
        k = KNUDSON_1983()
        self.assertEqual(k._HEIGHT_RANGES['m_6_11'],   (111.8, 154.9))
        self.assertEqual(k._HEIGHT_RANGES['m_12_24'],  (139.7, 193.0))
        self.assertEqual(k._HEIGHT_RANGES['m_25plus'], (157.5, 195.6))
        self.assertEqual(k._HEIGHT_RANGES['f_6_10'],   (106.7, 147.3))
        self.assertEqual(k._HEIGHT_RANGES['f_11_19'],  (132.1, 182.9))
        self.assertEqual(k._HEIGHT_RANGES['f_20_69'],  (147.3, 180.3))
        self.assertEqual(k._HEIGHT_RANGES['f_70plus'], (147.3, 167.6))

    def test_parameters_enum(self):
        params = [p.name for p in KNUDSON_1983.Parameters]
        for name in ('FVC', 'FEV1', 'FEF50', 'FEF75', 'FEF25_75', 'FEV1FVC'):
            self.assertIn(name, params)


class TestKnudson1983AgeGroups(unittest.TestCase):
    """Age-group routing produces different predictions across strata."""

    def setUp(self):
        self.k = KNUDSON_1983()

    def test_male_child_group(self):
        # age 8 → m_6_11
        result = self.k.percent(M, 8, 125, parameter=KNUDSON_1983.Parameters.FVC, value=1.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_male_adolescent_group(self):
        # age 16 → m_12_24
        result = self.k.percent(M, 16, 165, parameter=KNUDSON_1983.Parameters.FVC, value=4.0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_male_adult_group(self):
        # age 40 → m_25plus
        result = self.k.percent(M, 40, 175, parameter=KNUDSON_1983.Parameters.FVC, value=4.0)
        self.assertAlmostEqual(result, 83.4, places=1)

    def test_female_young_child_group(self):
        # age 8 → f_6_10
        result = self.k.percent(F, 8, 120, parameter=KNUDSON_1983.Parameters.FVC, value=1.2)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_female_adolescent_group(self):
        # age 15 → f_11_19
        result = self.k.percent(F, 15, 158, parameter=KNUDSON_1983.Parameters.FVC, value=3.0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_female_adult_group(self):
        # age 40 → f_20_69
        result = self.k.percent(F, 40, 163, parameter=KNUDSON_1983.Parameters.FVC, value=3.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_female_elderly_group(self):
        # age 75 → f_70plus
        result = self.k.percent(F, 75, 160, parameter=KNUDSON_1983.Parameters.FVC, value=2.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_known_child_fvc_male(self):
        result = self.k.percent(M, 8, 125, parameter=KNUDSON_1983.Parameters.FVC, value=1.5)
        self.assertAlmostEqual(result, 86.36, places=1)

    def test_groups_give_different_predictions(self):
        # Different age groups → different predicted FVC (heights must be in each stratum's range)
        pred_child = self.k.percent(M, 8, 130, parameter=KNUDSON_1983.Parameters.FVC, value=2.0)   # m_6_11: 111.8–154.9
        pred_adult = self.k.percent(M, 40, 175, parameter=KNUDSON_1983.Parameters.FVC, value=4.0)  # m_25plus: 157.5–195.6
        self.assertIsInstance(pred_child, float)
        self.assertIsInstance(pred_adult, float)
        self.assertNotAlmostEqual(pred_child, pred_adult, places=1)

    def test_stratum_height_below_range_returns_na(self):
        # Adult male (m_25plus) minimum height is 157.5 cm; 140 cm is below that
        result = self.k.percent(M, 40, 140, parameter=KNUDSON_1983.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))

    def test_stratum_height_above_child_range_returns_na(self):
        # Male child (m_6_11) maximum height is 154.9 cm; 160 cm is above that
        result = self.k.percent(M, 8, 160, parameter=KNUDSON_1983.Parameters.FVC, value=2.0)
        self.assertTrue(pd.isna(result))


class TestKnudson1983NoLLN(unittest.TestCase):

    def setUp(self):
        self.k = KNUDSON_1983()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.k.lln(M, 40, 175, parameter=KNUDSON_1983.Parameters.FVC, value=4.0)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.k.uln(M, 40, 175, parameter=KNUDSON_1983.Parameters.FVC, value=4.0)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.k.zscore(M, 40, 175, parameter=KNUDSON_1983.Parameters.FVC, value=4.0)))


class TestKnudson1983OutOfRange(unittest.TestCase):

    def setUp(self):
        self.k = KNUDSON_1983()

    def test_male_age_below_range_returns_na(self):
        result = self.k.percent(M, 5, 115, parameter=KNUDSON_1983.Parameters.FVC, value=1.0)
        self.assertTrue(pd.isna(result))

    def test_male_age_above_range_returns_na(self):
        result = self.k.percent(M, 91, 170, parameter=KNUDSON_1983.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))

    def test_female_age_above_range_returns_na(self):
        result = self.k.percent(F, 89, 160, parameter=KNUDSON_1983.Parameters.FVC, value=2.5)
        self.assertTrue(pd.isna(result))

    def test_male_height_below_range_returns_na(self):
        result = self.k.percent(M, 40, 111, parameter=KNUDSON_1983.Parameters.FVC, value=3.0)
        self.assertTrue(pd.isna(result))

    def test_female_height_above_range_returns_na(self):
        result = self.k.percent(F, 40, 184, parameter=KNUDSON_1983.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

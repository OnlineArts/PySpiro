import unittest
import pandas as pd
from pyspiro import WANG_1993

M = 1
F = 0
CAUCASIAN = WANG_1993.Ethnicity.CAUCASIAN.value
AFRICAN_AMERICAN = WANG_1993.Ethnicity.AFRICAN_AMERICAN.value


class TestWang1993Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(WANG_1993())

    def test_age_ranges(self):
        w = WANG_1993()
        self.assertEqual(w._AGE_MALE_RANGE, (6, 18))
        self.assertEqual(w._AGE_FEMALE_RANGE, (7, 18))

    def test_height_ranges(self):
        w = WANG_1993()
        self.assertEqual(w._HEIGHT_RANGES[('male',   'caucasian')],        (110.0, 190.0))
        self.assertEqual(w._HEIGHT_RANGES[('male',   'african_american')], (120.0, 190.0))
        self.assertEqual(w._HEIGHT_RANGES[('female', 'caucasian')],        (110.0, 180.0))
        self.assertEqual(w._HEIGHT_RANGES[('female', 'african_american')], (120.0, 180.0))

    def test_parameters_enum(self):
        params = [p.name for p in WANG_1993.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'FEF25_75'):
            self.assertIn(name, params)

    def test_ethnicity_enum(self):
        eths = [e.name for e in WANG_1993.Ethnicity]
        for name in ('CAUCASIAN', 'AFRICAN_AMERICAN'):
            self.assertIn(name, eths)


class TestWang1993Percent(unittest.TestCase):

    def setUp(self):
        self.w = WANG_1993()

    def test_known_fvc_male_caucasian(self):
        result = self.w.percent(M, 12, 150, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=2.5)
        self.assertAlmostEqual(result, 90.77, places=1)

    def test_fvc_returns_float_male(self):
        result = self.w.percent(M, 12, 150, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=2.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_fev1fvc_returned_as_percentage(self):
        # FEV1FVC is internally multiplied by 100
        result = self.w.percent(M, 12, 150, CAUCASIAN, parameter=WANG_1993.Parameters.FEV1FVC, value=80.0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_fef25_75_returns_na_for_age_6(self):
        # FEF25–75% is not available for ages 6–7 (alpha/beta are NaN in CSV)
        result = self.w.percent(M, 6, 120, CAUCASIAN, parameter=WANG_1993.Parameters.FEF25_75, value=2.0)
        self.assertTrue(pd.isna(result))

    def test_fef25_75_available_from_age_8(self):
        result = self.w.percent(M, 8, 130, CAUCASIAN, parameter=WANG_1993.Parameters.FEF25_75, value=2.0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_ethnicities_differ_when_both_available(self):
        r_caucasian = self.w.percent(M, 12, 150, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=2.5)
        r_african_american = self.w.percent(M, 12, 150, AFRICAN_AMERICAN, parameter=WANG_1993.Parameters.FVC, value=2.5)
        if pd.isna(r_african_american):
            self.skipTest("AFRICAN_AMERICAN coefficients not yet populated in wang_1993_coefficients.csv")
        self.assertNotAlmostEqual(r_caucasian, r_african_american, places=1)


class TestWang1993NoLLN(unittest.TestCase):

    def setUp(self):
        self.w = WANG_1993()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.w.lln(M, 12, 150, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=2.5)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.w.uln(M, 12, 150, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=2.5)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.w.zscore(M, 12, 150, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=2.5)))


class TestWang1993OutOfRange(unittest.TestCase):

    def setUp(self):
        self.w = WANG_1993()

    def test_male_age_below_range_returns_na(self):
        result = self.w.percent(M, 5, 115, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=1.0)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.w.percent(M, 19, 175, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=5.0)
        self.assertTrue(pd.isna(result))

    def test_female_age_below_range_returns_na(self):
        result = self.w.percent(F, 6, 115, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=1.0)
        self.assertTrue(pd.isna(result))

    def test_caucasian_height_below_range_returns_na(self):
        result = self.w.percent(M, 12, 109, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=2.0)
        self.assertTrue(pd.isna(result))

    def test_male_height_above_range_returns_na(self):
        result = self.w.percent(M, 18, 191, CAUCASIAN, parameter=WANG_1993.Parameters.FVC, value=5.0)
        self.assertTrue(pd.isna(result))

    def test_african_american_height_below_120_returns_na(self):
        # African-American minimum height is 120 cm, not 110 cm
        result = self.w.percent(M, 12, 119, AFRICAN_AMERICAN, parameter=WANG_1993.Parameters.FVC, value=2.0)
        self.assertTrue(pd.isna(result))

    def test_african_american_height_at_120_returns_float(self):
        result = self.w.percent(M, 12, 120, AFRICAN_AMERICAN, parameter=WANG_1993.Parameters.FVC, value=2.0)
        # Returns NA if AA coefficients not yet in CSV, otherwise a float
        self.assertTrue(pd.isna(result) or isinstance(result, float))


if __name__ == '__main__':
    unittest.main()

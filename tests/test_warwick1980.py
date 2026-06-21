import unittest
import pandas as pd
from pyspiro import WARWICK_1980

M = 1
F = 0


class TestWarwick1980Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(WARWICK_1980())

    def test_age_range(self):
        w = WARWICK_1980()
        self.assertEqual(w._age_range, (0, 18))

    def test_height_ranges(self):
        w = WARWICK_1980()
        self.assertEqual(w._HEIGHT_MALE_RANGE, (90.0, 188.0))
        self.assertEqual(w._HEIGHT_FEMALE_RANGE, (90.0, 178.0))

    def test_parameters_enum(self):
        params = [p.name for p in WARWICK_1980.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'FEF50', 'FEF75', 'PEFR', 'FET'):
            self.assertIn(name, params)


class TestWarwick1980Percent(unittest.TestCase):

    def setUp(self):
        self.w = WARWICK_1980()

    def test_known_fvc_male(self):
        result = self.w.percent(M, 10, 130, parameter=WARWICK_1980.Parameters.FVC, value=1.5)
        self.assertAlmostEqual(result, 81.27, places=1)

    def test_all_parameters_return_float_male(self):
        for param in WARWICK_1980.Parameters:
            with self.subTest(param=param.name):
                result = self.w.percent(M, 10, 130, parameter=param, value=1.5)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in WARWICK_1980.Parameters:
            with self.subTest(param=param.name):
                result = self.w.percent(F, 10, 128, parameter=param, value=1.5)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_fev1fvc_returned_as_percentage(self):
        # FEV1FVC result is multiplied by 100
        result = self.w.percent(M, 10, 130, parameter=WARWICK_1980.Parameters.FEV1FVC, value=80.0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_male_differs_from_female(self):
        r_m = self.w.percent(M, 10, 130, parameter=WARWICK_1980.Parameters.FVC, value=1.5)
        r_f = self.w.percent(F, 10, 128, parameter=WARWICK_1980.Parameters.FVC, value=1.5)
        self.assertNotAlmostEqual(r_m, r_f, places=1)

    def test_prediction_scales_with_height(self):
        r_small = self.w.percent(M, 10, 120, parameter=WARWICK_1980.Parameters.FVC, value=1.5)
        r_tall = self.w.percent(M, 10, 150, parameter=WARWICK_1980.Parameters.FVC, value=1.5)
        # Taller child → higher predicted FVC → lower percent for same value
        self.assertGreater(r_small, r_tall)


class TestWarwick1980NoLLN(unittest.TestCase):

    def setUp(self):
        self.w = WARWICK_1980()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.w.lln(M, 10, 130, parameter=WARWICK_1980.Parameters.FVC, value=1.5)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.w.uln(M, 10, 130, parameter=WARWICK_1980.Parameters.FVC, value=1.5)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.w.zscore(M, 10, 130, parameter=WARWICK_1980.Parameters.FVC, value=1.5)))


class TestWarwick1980OutOfRange(unittest.TestCase):

    def setUp(self):
        self.w = WARWICK_1980()

    def test_age_above_range_returns_na(self):
        result = self.w.percent(M, 19, 175, parameter=WARWICK_1980.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_height_below_range_returns_na(self):
        result = self.w.percent(M, 5, 89, parameter=WARWICK_1980.Parameters.FVC, value=0.5)
        self.assertTrue(pd.isna(result))

    def test_male_height_above_range_returns_na(self):
        result = self.w.percent(M, 17, 189, parameter=WARWICK_1980.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))

    def test_female_height_above_range_returns_na(self):
        # Female max is 178 cm (shorter than male max of 188 cm)
        result = self.w.percent(F, 17, 179, parameter=WARWICK_1980.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

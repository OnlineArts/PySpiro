import unittest
import pandas as pd
from pyspiro import QUANJER_1995

M = 1
F = 0


class TestQuanjer1995Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(QUANJER_1995())

    def test_age_range(self):
        q = QUANJER_1995()
        self.assertEqual(q._age_range, (6, 18))

    def test_height_ranges(self):
        q = QUANJER_1995()
        self.assertEqual(q._HEIGHT_MALE_RANGE, (110.0, 205.0))
        self.assertEqual(q._HEIGHT_FEMALE_RANGE, (110.0, 185.0))

    def test_parameters_enum(self):
        params = [p.name for p in QUANJER_1995.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC'):
            self.assertIn(name, params)


class TestQuanjer1995Percent(unittest.TestCase):

    def setUp(self):
        self.q = QUANJER_1995()

    def test_known_fvc_male(self):
        result = self.q.percent(M, 14, 155, parameter=QUANJER_1995.Parameters.FVC, value=3.0)
        self.assertAlmostEqual(result, 89.82, places=1)

    def test_fev1fvc_is_constant_per_sex(self):
        # FEV1FVC is a sex-specific constant (not dependent on age or height)
        r1 = self.q.percent(M, 10, 130, parameter=QUANJER_1995.Parameters.FEV1FVC, value=80.0)
        r2 = self.q.percent(M, 16, 170, parameter=QUANJER_1995.Parameters.FEV1FVC, value=80.0)
        self.assertAlmostEqual(r1, r2, places=5)

    def test_fvc_scales_with_height(self):
        r_small = self.q.percent(M, 14, 140, parameter=QUANJER_1995.Parameters.FVC, value=3.0)
        r_tall = self.q.percent(M, 14, 170, parameter=QUANJER_1995.Parameters.FVC, value=3.0)
        # Taller child → higher predicted FVC → lower percent for same value
        self.assertGreater(r_small, r_tall)

    def test_all_parameters_return_float_male(self):
        for param in QUANJER_1995.Parameters:
            with self.subTest(param=param.name):
                result = self.q.percent(M, 14, 155, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_all_parameters_return_float_female(self):
        for param in QUANJER_1995.Parameters:
            with self.subTest(param=param.name):
                result = self.q.percent(F, 14, 150, parameter=param, value=3.0)
                self.assertIsInstance(result, float)
                self.assertGreater(result, 0)

    def test_male_fvc_differs_from_female(self):
        r_m = self.q.percent(M, 14, 155, parameter=QUANJER_1995.Parameters.FVC, value=3.0)
        r_f = self.q.percent(F, 14, 150, parameter=QUANJER_1995.Parameters.FVC, value=3.0)
        self.assertNotAlmostEqual(r_m, r_f, places=1)


class TestQuanjer1995NoLLN(unittest.TestCase):

    def setUp(self):
        self.q = QUANJER_1995()

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.q.lln(M, 14, 155, parameter=QUANJER_1995.Parameters.FVC, value=3.0)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.q.uln(M, 14, 155, parameter=QUANJER_1995.Parameters.FVC, value=3.0)))

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.q.zscore(M, 14, 155, parameter=QUANJER_1995.Parameters.FVC, value=3.0)))


class TestQuanjer1995OutOfRange(unittest.TestCase):

    def setUp(self):
        self.q = QUANJER_1995()

    def test_age_below_range_returns_na(self):
        result = self.q.percent(M, 5, 130, parameter=QUANJER_1995.Parameters.FVC, value=1.5)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.q.percent(M, 19, 170, parameter=QUANJER_1995.Parameters.FVC, value=5.0)
        self.assertTrue(pd.isna(result))

    def test_male_height_below_range_returns_na(self):
        result = self.q.percent(M, 12, 109, parameter=QUANJER_1995.Parameters.FVC, value=2.0)
        self.assertTrue(pd.isna(result))

    def test_female_height_above_range_returns_na(self):
        result = self.q.percent(F, 14, 186, parameter=QUANJER_1995.Parameters.FVC, value=4.0)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

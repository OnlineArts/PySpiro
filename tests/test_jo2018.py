import unittest
import pandas as pd
from pyspiro import JO_2018

M = 1
F = 0


class TestJo2018Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(JO_2018())

    def test_age_range(self):
        j = JO_2018()
        self.assertEqual(j._age_range, (19, 90))

    def test_parameters_enum(self):
        params = [p.name for p in JO_2018.Parameters]
        for name in ('FEV1', 'FVC', 'FEV1FVC'):
            self.assertIn(name, params)


class TestJo2018LMS(unittest.TestCase):

    def setUp(self):
        self.j = JO_2018()

    def test_lms_returns_three_floats_male(self):
        l, m, s = self.j.lms(M, 40, 175, JO_2018.Parameters.FEV1)
        self.assertIsInstance(l, float)
        self.assertIsInstance(m, float)
        self.assertIsInstance(s, float)

    def test_lms_returns_three_floats_female(self):
        l, m, s = self.j.lms(F, 40, 163, JO_2018.Parameters.FVC)
        self.assertIsInstance(l, float)
        self.assertIsInstance(m, float)
        self.assertIsInstance(s, float)

    def test_m_is_positive(self):
        _, m, _ = self.j.lms(M, 40, 175, JO_2018.Parameters.FEV1)
        self.assertGreater(m, 0)

    def test_s_is_positive(self):
        _, _, s = self.j.lms(M, 40, 175, JO_2018.Parameters.FEV1)
        self.assertGreater(s, 0)

    def test_all_parameters_return_valid_lms_male(self):
        for param in JO_2018.Parameters:
            with self.subTest(param=param.name):
                l, m, s = self.j.lms(M, 40, 175, param)
                self.assertFalse(pd.isna(m))
                self.assertFalse(pd.isna(s))

    def test_male_differs_from_female(self):
        _, m_m, _ = self.j.lms(M, 40, 175, JO_2018.Parameters.FEV1)
        _, m_f, _ = self.j.lms(F, 40, 163, JO_2018.Parameters.FEV1)
        self.assertNotAlmostEqual(m_m, m_f, places=2)


class TestJo2018Percent(unittest.TestCase):

    def setUp(self):
        self.j = JO_2018()

    def test_known_fev1_male(self):
        result = self.j.percent(M, 40, 175, JO_2018.Parameters.FEV1, 3.5)
        self.assertAlmostEqual(result, 88.81, places=1)

    def test_percent_returns_float(self):
        result = self.j.percent(M, 40, 175, JO_2018.Parameters.FVC, 4.0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_higher_value_gives_higher_percent(self):
        r_low = self.j.percent(M, 40, 175, JO_2018.Parameters.FEV1, 3.0)
        r_high = self.j.percent(M, 40, 175, JO_2018.Parameters.FEV1, 4.0)
        self.assertGreater(r_high, r_low)


class TestJo2018LLN(unittest.TestCase):

    def setUp(self):
        self.j = JO_2018()

    def test_lln_returns_float(self):
        result = self.j.lln(M, 40, 175, JO_2018.Parameters.FEV1, 3.5)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_lln_less_than_predicted(self):
        lln = self.j.lln(M, 40, 175, JO_2018.Parameters.FEV1, 3.5)
        _, m, _ = self.j.lms(M, 40, 175, JO_2018.Parameters.FEV1)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted(self):
        uln = self.j.uln(M, 40, 175, JO_2018.Parameters.FEV1, 3.5)
        _, m, _ = self.j.lms(M, 40, 175, JO_2018.Parameters.FEV1)
        self.assertGreater(uln, m)

    def test_zscore_sign_correct(self):
        # A value equal to the predicted median should have z-score ≈ 0
        _, m, _ = self.j.lms(M, 40, 175, JO_2018.Parameters.FEV1)
        zscore = self.j.zscore(M, 40, 175, JO_2018.Parameters.FEV1, m)
        self.assertAlmostEqual(zscore, 0.0, places=3)


class TestJo2018OutOfRange(unittest.TestCase):

    def setUp(self):
        self.j = JO_2018()

    def test_age_below_range_returns_na(self):
        l, m, s = self.j.lms(M, 18, 175, JO_2018.Parameters.FEV1)
        self.assertTrue(pd.isna(m))

    def test_age_above_range_returns_na(self):
        l, m, s = self.j.lms(M, 91, 175, JO_2018.Parameters.FEV1)
        self.assertTrue(pd.isna(m))

    def test_percent_out_of_range_returns_na(self):
        result = self.j.percent(M, 18, 175, JO_2018.Parameters.FEV1, 3.5)
        self.assertTrue(pd.isna(result))


if __name__ == '__main__':
    unittest.main()

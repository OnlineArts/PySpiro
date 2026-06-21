import unittest
import pandas as pd
from pyspiro import BOWERMAN_2022


M = 1
F = 0


class TestBowerman2022Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(BOWERMAN_2022())


class TestBowerman2022Percent(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_percent_known_fvc_male(self):
        # Male, 40y, 175 cm, FVC=4.5 L → 95.77%
        result = self.bow.percent(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        self.assertAlmostEqual(result, 95.77, places=1)

    def test_percent_at_median_is_100(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 0)
        result = self.bow.percent(M, 40, 175, BOWERMAN_2022.Parameters.FVC, m)
        self.assertAlmostEqual(result, 100.0, places=1)

    def test_fev1_fvc_and_fev1fvc_return_float(self):
        for param in [BOWERMAN_2022.Parameters.FEV1, BOWERMAN_2022.Parameters.FVC,
                      BOWERMAN_2022.Parameters.FEV1FVC]:
            with self.subTest(param=param.name):
                result = self.bow.percent(M, 40, 175, param, 3.0)
                self.assertFalse(pd.isna(result))

    def test_fev1fvc_female_returns_float(self):
        # FEV1FVC female splines are present in the CSV
        result = self.bow.percent(F, 40, 165, BOWERMAN_2022.Parameters.FEV1FVC, 0.78)
        self.assertFalse(pd.isna(result))

    def test_female_differs_from_male(self):
        p_m = self.bow.percent(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        p_f = self.bow.percent(F, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        self.assertNotAlmostEqual(p_m, p_f, places=1)


class TestBowerman2022ZScore(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_zscore_below_median_is_negative(self):
        # FVC=4.5 L is below median for 40yo male → negative z
        result = self.bow.zscore(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 4.5)
        self.assertLess(result, 0)

    def test_zscore_at_median_is_zero(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FVC, 0)
        result = self.bow.zscore(M, 40, 175, BOWERMAN_2022.Parameters.FVC, m)
        self.assertAlmostEqual(result, 0.0, places=5)


class TestBowerman2022LimitsOfNormal(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_lln_less_than_predicted(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, 0)
        lln = self.bow.lln(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, m)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted(self):
        l, m, s = self.bow.lms(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, 0)
        uln = self.bow.uln(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, m)
        self.assertGreater(uln, m)

    def test_lln_zscore_is_minus_1645(self):
        lln = self.bow.lln(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, 0)
        z = self.bow.zscore(M, 40, 175, BOWERMAN_2022.Parameters.FEV1, lln)
        self.assertAlmostEqual(z, -1.645, places=2)


class TestBowerman2022OutOfRange(unittest.TestCase):

    def setUp(self):
        self.bow = BOWERMAN_2022()

    def test_age_out_of_range_returns_na(self):
        result = self.bow.percent(M, 200, 175, BOWERMAN_2022.Parameters.FEV1, 3.0)
        self.assertTrue(pd.isna(result))


if __name__ == "__main__":
    unittest.main()

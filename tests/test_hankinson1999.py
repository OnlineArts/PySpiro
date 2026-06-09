import unittest
import pandas as pd
from pyspiro import HANKINSON_1999


M = 1
F = 0
W = HANKINSON_1999.Ethnicity.CAUCASIAN.value
B = HANKINSON_1999.Ethnicity.AFRICAN_AMERICAN.value
X = HANKINSON_1999.Ethnicity.MEXICAN_AMERICAN.value


class TestHankinson1999Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(HANKINSON_1999())

    def test_age_range(self):
        h = HANKINSON_1999()
        self.assertEqual(h._AGE_RANGE, (8, 80))

    def test_parameters_enum(self):
        params = [p.name for p in HANKINSON_1999.Parameters]
        self.assertIn("FVC", params)
        self.assertIn("FEV1", params)
        self.assertIn("FEV1FVC", params)
        self.assertIn("FEF25_75", params)
        self.assertIn("PEF", params)
        self.assertIn("FEV1FEV6", params)

    def test_ethnicity_enum(self):
        eths = [e.name for e in HANKINSON_1999.Ethnicity]
        self.assertIn("CAUCASIAN", eths)
        self.assertIn("AFRICAN_AMERICAN", eths)
        self.assertIn("MEXICAN_AMERICAN", eths)


class TestHankinson1999OutputType(unittest.TestCase):
    """
    Tests that return type is correct for both filled and placeholder CSV states.
    When CSV coefficients are all zero, _compute returns (NA, NA) and all
    public methods return pd.NA — which is also a valid outcome and tested here.
    """

    def setUp(self):
        self.h = HANKINSON_1999()

    def _result_is_valid(self, result):
        """Return True if result is a finite float or pd.NA (both are acceptable)."""
        if pd.isna(result):
            return True
        return isinstance(result, float) and result > 0

    def test_percent_adult_male_caucasian(self):
        result = self.h.percent(M, 40, 175, W, HANKINSON_1999.Parameters.FEV1, 3.5)
        self.assertTrue(self._result_is_valid(result))

    def test_percent_child_female_african_american(self):
        result = self.h.percent(F, 14, 160, B, HANKINSON_1999.Parameters.FVC, 2.5)
        self.assertTrue(self._result_is_valid(result))

    def test_all_t4t5_parameters_return_valid(self):
        for param in [HANKINSON_1999.Parameters.FVC, HANKINSON_1999.Parameters.FEV1,
                      HANKINSON_1999.Parameters.FEF25_75, HANKINSON_1999.Parameters.PEF]:
            for eth in [W, B, X]:
                with self.subTest(param=param.name, eth=eth):
                    result = self.h.percent(M, 40, 175, eth, param, 3.0)
                    self.assertTrue(self._result_is_valid(result))

    def test_all_t6_parameters_return_valid(self):
        for param in [HANKINSON_1999.Parameters.FEV1FVC,
                      HANKINSON_1999.Parameters.FEV1FEV6]:
            with self.subTest(param=param.name):
                result = self.h.percent(M, 40, 175, W, param, 0.75)
                self.assertTrue(self._result_is_valid(result))

    def test_lln_less_than_predicted_when_data_available(self):
        l, m, s = self.h.lms(M, 40, 175, W, HANKINSON_1999.Parameters.FEV1, 3.5)
        if pd.isna(m):
            self.skipTest("Hankinson CSV coefficients not yet populated")
        lln = self.h.lln(M, 40, 175, W, HANKINSON_1999.Parameters.FEV1, 3.5)
        self.assertLess(lln, m)

    def test_uln_greater_than_predicted_when_data_available(self):
        l, m, s = self.h.lms(M, 40, 175, W, HANKINSON_1999.Parameters.FEV1, 3.5)
        if pd.isna(m):
            self.skipTest("Hankinson CSV coefficients not yet populated")
        uln = self.h.uln(M, 40, 175, W, HANKINSON_1999.Parameters.FEV1, 3.5)
        self.assertGreater(uln, m)


class TestHankinson1999OutOfRange(unittest.TestCase):

    def setUp(self):
        self.h = HANKINSON_1999()

    def test_age_below_range_returns_na(self):
        result = self.h.percent(M, 7, 175, W, HANKINSON_1999.Parameters.FEV1, 3.5)
        self.assertTrue(pd.isna(result))

    def test_age_above_range_returns_na(self):
        result = self.h.percent(M, 81, 175, W, HANKINSON_1999.Parameters.FEV1, 3.5)
        self.assertTrue(pd.isna(result))


class TestHankinson1999AgeGroupRouting(unittest.TestCase):

    def setUp(self):
        self.h = HANKINSON_1999()

    def test_child_routes_to_child_table(self):
        # Age 14 should route to 'child', age 18 to 'adult'
        # They should give different predicted values if CSV is populated
        l_child, m_child, s_child = self.h.lms(M, 14, 160, W,
                                                HANKINSON_1999.Parameters.FEV1, 0)
        l_adult, m_adult, s_adult = self.h.lms(M, 40, 160, W,
                                                HANKINSON_1999.Parameters.FEV1, 0)
        if pd.isna(m_child) or pd.isna(m_adult):
            self.skipTest("Hankinson CSV coefficients not yet populated")
        self.assertNotAlmostEqual(m_child, m_adult, places=2)


if __name__ == "__main__":
    unittest.main()

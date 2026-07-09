import unittest
import pandas as pd
from pyspiro import ALQEREM_2019

M = 1
F = 0
P = ALQEREM_2019.Parameters


class TestAlqerem2019Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(ALQEREM_2019())

    def test_age_ranges(self):
        a = ALQEREM_2019()
        self.assertEqual(a._age_range(M), (18, 83))
        self.assertEqual(a._age_range(F), (18, 78))

    def test_height_range(self):
        self.assertEqual(ALQEREM_2019()._height_range, (140, 200))

    def test_parameters_enum(self):
        names = [p.name for p in ALQEREM_2019.Parameters]
        for name in ('FEV1', 'FVC', 'FEV1FVC', 'FEF75', 'FEF2575', 'FEF25', 'FEF50'):
            self.assertIn(name, names)


class TestAlqerem2019Table2CrossCheck(unittest.TestCase):
    """
    Cross-check predicted means against Al Qerem et al. 2019 Table 2 (sample means
    reported at the mean age/height of each sex). The paper publishes no
    per-subject worked examples, so Table 2 provides the manuscript reference.

        Males   (n=888):  age 38.12 yr, height 173.09 cm
        Females (n=1061): age 37.51 yr, height 158.42 cm

    Small discrepancies are expected because the prediction is evaluated at the
    mean age rather than averaged over the (right-skewed) age distribution.
    """

    def setUp(self):
        self.a = ALQEREM_2019()

    def _check(self, sex, age, height, param, expected, delta=0.25):
        got = self.a.predicted(sex, age, height, param)
        self.assertAlmostEqual(got, expected, delta=delta,
                               msg=f'{param.name} sex={sex}: got {got:.3f}, Table 2 = {expected}')

    def test_male_fev1(self):    self._check(M, 38.12, 173.09, P.FEV1,    3.71)
    def test_male_fvc(self):     self._check(M, 38.12, 173.09, P.FVC,     4.35)
    def test_male_fev1fvc(self): self._check(M, 38.12, 173.09, P.FEV1FVC, 85.80, delta=1.5)
    def test_male_fef75(self):   self._check(M, 38.12, 173.09, P.FEF75,   2.14)
    def test_male_fef2575(self): self._check(M, 38.12, 173.09, P.FEF2575, 4.32)
    def test_male_fef25(self):   self._check(M, 38.12, 173.09, P.FEF25,   6.856)
    def test_male_fef50(self):   self._check(M, 38.12, 173.09, P.FEF50,   4.85)

    def test_female_fev1(self):    self._check(F, 37.51, 158.42, P.FEV1,    2.63)
    def test_female_fvc(self):     self._check(F, 37.51, 158.42, P.FVC,     3.00)
    def test_female_fev1fvc(self): self._check(F, 37.51, 158.42, P.FEV1FVC, 87.99, delta=1.5)
    def test_female_fef75(self):   self._check(F, 37.51, 158.42, P.FEF75,   1.74)
    def test_female_fef2575(self): self._check(F, 37.51, 158.42, P.FEF2575, 3.28)
    def test_female_fef25(self):   self._check(F, 37.51, 158.42, P.FEF25,   4.83)
    def test_female_fef50(self):   self._check(F, 37.51, 158.42, P.FEF50,   3.62)


class TestAlqerem2019PredictedRegression(unittest.TestCase):
    """Exact predicted values (regression guard) at age 40, male 173 cm / female 160 cm."""

    def setUp(self):
        self.a = ALQEREM_2019()

    def _check(self, sex, height, param, expected):
        self.assertAlmostEqual(self.a.predicted(sex, 40, height, param), expected, places=4)

    def test_m_fev1(self):    self._check(M, 173, P.FEV1,    3.63509)
    def test_m_fvc(self):     self._check(M, 173, P.FVC,     4.20390)
    def test_m_fev1fvc(self): self._check(M, 173, P.FEV1FVC, 86.43301)
    def test_m_fef75(self):   self._check(M, 173, P.FEF75,   1.96088)
    def test_m_fef2575(self): self._check(M, 173, P.FEF2575, 4.28381)
    def test_m_fef25(self):   self._check(M, 173, P.FEF25,   6.98337)
    def test_m_fef50(self):   self._check(M, 173, P.FEF50,   4.90055)

    def test_f_fev1(self):    self._check(F, 160, P.FEV1,    2.62616)
    def test_f_fvc(self):     self._check(F, 160, P.FVC,     3.01697)
    def test_f_fev1fvc(self): self._check(F, 160, P.FEV1FVC, 88.19366)
    def test_f_fef75(self):   self._check(F, 160, P.FEF75,   1.56300)
    def test_f_fef2575(self): self._check(F, 160, P.FEF2575, 3.26318)
    def test_f_fef25(self):   self._check(F, 160, P.FEF25,   4.82620)
    def test_f_fef50(self):   self._check(F, 160, P.FEF50,   3.62267)


class TestAlqerem2019Metrics(unittest.TestCase):

    def setUp(self):
        self.a = ALQEREM_2019()

    def test_percent_at_mean_is_100(self):
        for sex, h in ((M, 173), (F, 160)):
            for p in ALQEREM_2019.Parameters:
                with self.subTest(sex=sex, param=p.name):
                    mu = self.a.predicted(sex, 40, h, p)
                    self.assertAlmostEqual(self.a.percent(sex, 40, h, p, mu), 100.0, places=2)

    def test_zscore_at_mean_is_zero(self):
        for sex, h in ((M, 173), (F, 160)):
            for p in ALQEREM_2019.Parameters:
                with self.subTest(sex=sex, param=p.name):
                    mu = self.a.predicted(sex, 40, h, p)
                    self.assertAlmostEqual(self.a.zscore(sex, 40, h, p, mu), 0.0, places=6)

    def test_lln_below_mean_uln_above(self):
        for sex, h in ((M, 173), (F, 160)):
            for p in ALQEREM_2019.Parameters:
                with self.subTest(sex=sex, param=p.name):
                    mu = self.a.predicted(sex, 40, h, p)
                    self.assertLess(self.a.lln(sex, 40, h, p), mu)
                    self.assertGreater(self.a.uln(sex, 40, h, p), mu)

    # Detailed values for a BCCG parameter (male FEF50, identity link, nu=1).
    def test_bccg_detail(self):
        p = P.FEF50
        self.assertAlmostEqual(self.a.lln(M, 40, 173, p), 2.74254, places=4)
        self.assertAlmostEqual(self.a.uln(M, 40, 173, p), 7.05856, places=4)
        self.assertAlmostEqual(self.a.percent(M, 40, 173, p, 5.0), 102.03, places=2)
        self.assertAlmostEqual(self.a.zscore(M, 40, 173, p, 5.0), 0.07581, places=4)

    # Detailed values for a Normal parameter (male FEV1).
    def test_normal_detail(self):
        p = P.FEV1
        self.assertAlmostEqual(self.a.lln(M, 40, 173, p), 2.82353, places=4)
        self.assertAlmostEqual(self.a.uln(M, 40, 173, p), 4.44664, places=4)
        self.assertAlmostEqual(self.a.zscore(M, 40, 173, p, 3.0), -1.28731, places=4)

    def test_fev1fvc_is_percentage(self):
        # FEV1/FVC predicted ~88% (percentage scale, not a 0-1 ratio)
        self.assertGreater(self.a.predicted(F, 40, 160, P.FEV1FVC), 50)
        self.assertAlmostEqual(self.a.zscore(F, 40, 160, P.FEV1FVC, 85.0), -0.41631, places=4)


class TestAlqerem2019LMS(unittest.TestCase):

    def setUp(self):
        self.a = ALQEREM_2019()

    def test_lms_bccg_returns_nu_mu_sigma(self):
        nu, mu, sigma = self.a.lms(M, 40, 173, P.FEF50)
        self.assertAlmostEqual(nu, 1.0, places=6)
        self.assertAlmostEqual(mu, 4.90055, places=4)
        self.assertGreater(sigma, 0)

    def test_lms_normal_not_applicable(self):
        # FEV1 males is a Normal (NO) model — lms not applicable
        self.assertEqual(self.a.lms(M, 40, 173, P.FEV1), (pd.NA, pd.NA, pd.NA))
        # FVC females is also Normal
        self.assertEqual(self.a.lms(F, 40, 160, P.FVC), (pd.NA, pd.NA, pd.NA))


class TestAlqerem2019Splines(unittest.TestCase):

    def setUp(self):
        self.a = ALQEREM_2019()

    def test_spline_lookup_value(self):
        # First row of male FEV1 spline table (supplementary Table 1, age 18.0)
        mspline, sspline = self.a._spline(M, 'FEV1', 18.0)
        self.assertAlmostEqual(mspline, -0.057944198, places=6)

    def test_no_spline_returns_zero(self):
        # FEV1/FVC uses no age-spline
        self.assertEqual(self.a._spline(M, 'FEV1FVC', 40.0), (0.0, 0.0))

    def test_prediction_varies_with_age(self):
        young = self.a.predicted(M, 20, 173, P.FEV1)
        old = self.a.predicted(M, 60, 173, P.FEV1)
        self.assertGreater(young, old)


class TestAlqerem2019OutOfRange(unittest.TestCase):

    def setUp(self):
        self.a = ALQEREM_2019()

    def test_male_age_above_range(self):
        self.assertTrue(pd.isna(self.a.predicted(M, 90, 173, P.FEV1)))

    def test_female_age_above_male_range_ok_but_female_range_not(self):
        # 80 yr is within male range (18-83) but outside female range (18-78)
        self.assertTrue(pd.isna(self.a.predicted(F, 80, 160, P.FEV1)))
        self.assertFalse(pd.isna(self.a.predicted(M, 80, 173, P.FEV1)))

    def test_age_below_range(self):
        self.assertTrue(pd.isna(self.a.predicted(M, 15, 173, P.FEV1)))

    def test_height_out_of_range(self):
        self.assertTrue(pd.isna(self.a.predicted(M, 40, 210, P.FEV1)))

    def test_percent_out_of_range(self):
        self.assertTrue(pd.isna(self.a.percent(M, 90, 173, P.FEV1, 3.0)))


class TestAlqerem2019Compute(unittest.TestCase):

    def setUp(self):
        self.a = ALQEREM_2019()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 30.0],
            'height': [173.0, 160.0],
            'FEV1':   [3.6, 2.6],
        })

    def test_compute_returns_dataframe(self):
        result = self.a.compute(self.df, P.FEV1, value_col='FEV1')
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

    def test_compute_columns_present(self):
        result = self.a.compute(self.df, P.FEV1, value_col='FEV1',
                                metrics=('percent', 'zscore', 'lln', 'uln'))
        for col in ('percent', 'zscore', 'lln', 'uln'):
            self.assertIn(col, result.columns)


if __name__ == '__main__':
    unittest.main()

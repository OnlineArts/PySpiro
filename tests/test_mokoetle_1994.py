import unittest
import pandas as pd
from pyspiro import MOKOETLE_1994

M = 1
F = 0

FVC = MOKOETLE_1994.Parameters.FVC.value
FEV1 = MOKOETLE_1994.Parameters.FEV1.value


def predicted(eq, sex, age, height, parameter):
    """Predicted value in litres. percent() rounds to 2 dp, so go via _compute()."""
    return eq._compute(sex, age, height, parameter)


class TestMokoetle1994Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(MOKOETLE_1994())

    def test_parameters_enum(self):
        params = [p.name for p in MOKOETLE_1994.Parameters]
        for name in ('FVC', 'FEV1'):
            self.assertIn(name, params)


class TestMokoetle1994Coefficients(unittest.TestCase):
    """Standing-height equations as published in the Results section."""

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_men_fvc(self):
        # FVC = 0.053 (standing height) - 0.021 (age) - 3.85  (R2 = 0.427)
        self.assertAlmostEqual(predicted(self.eq, M, 35, 170, FVC), 4.425, places=3)

    def test_men_fev1(self):
        # FEV1 = 0.035 (standing height) - 0.036 (age) - 1.15  (R2 = 0.507)
        self.assertAlmostEqual(predicted(self.eq, M, 35, 170, FEV1), 3.540, places=3)

    def test_women_fvc(self):
        # FVC = 0.045 (standing height) - 0.023 (age) - 3.04  (R2 = 0.370)
        self.assertAlmostEqual(predicted(self.eq, F, 35, 160, FVC), 3.355, places=3)

    def test_women_fev1(self):
        # FEV1 = 0.034 (standing height) - 0.028 (age) - 1.87  (R2 = 0.388)
        self.assertAlmostEqual(predicted(self.eq, F, 35, 160, FEV1), 2.590, places=3)


class TestMokoetle1994PublishedWorkedExamples(unittest.TestCase):
    """The paper tabulates its own predictions alongside earlier South African studies."""

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_men_table6_fvc_age35_height170(self):
        # Table 6, 'This study': FVC predicted for age 35, ht 170 cm = 4.42
        self.assertAlmostEqual(predicted(self.eq, M, 35, 170, FVC), 4.42, delta=0.01)

    def test_women_table7_fvc_age35_height160(self):
        # Table 7, 'This study': FVC predicted for age 35, ht 160 cm = 3.35
        self.assertAlmostEqual(predicted(self.eq, F, 35, 160, FVC), 3.35, delta=0.01)


class TestMokoetle1994GroupMeans(unittest.TestCase):
    """Predictions at the study's mean age and height land on its observed means.

    Table 4 reports lung function standardised for height and split by smoking
    status, so these are consistency checks, not exact identities:
    men 168.7 cm / 42 y, FVC 4.04 (never) to 4.22 (ever), FEV1 3.27 to 3.33;
    women 158.0 cm / 41 y, FVC 3.09 to 3.17, FEV1 2.45 to 2.42.
    """

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_men_fvc_between_smoking_strata(self):
        pred = predicted(self.eq, M, 42, 168.7, FVC)
        self.assertGreater(pred, 4.04)
        self.assertLess(pred, 4.22)

    def test_men_fev1_near_observed(self):
        pred = predicted(self.eq, M, 42, 168.7, FEV1)
        self.assertAlmostEqual(pred, 3.30, delta=0.10)

    def test_women_fvc_between_smoking_strata(self):
        pred = predicted(self.eq, F, 41, 158.0, FVC)
        self.assertGreater(pred, 3.09)
        self.assertLess(pred, 3.17)

    def test_women_fev1_near_observed(self):
        pred = predicted(self.eq, F, 41, 158.0, FEV1)
        self.assertAlmostEqual(pred, 2.44, delta=0.10)


class TestMokoetle1994StandingHeightNotSitting(unittest.TestCase):
    """The paper also publishes sitting-height equations; those are not implemented.

    Standing height explained more of the variance, so only those are used here.
    Guard against a sitting-height coefficient being substituted by mistake.
    """

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_men_fvc_is_not_the_sitting_height_equation(self):
        # Sitting-height variant: 0.083 (sitting height) - 0.025 (age) - 1.83
        sitting = 0.083 * 170 - 0.025 * 35 - 1.83
        self.assertNotAlmostEqual(predicted(self.eq, M, 35, 170, FVC), sitting, places=2)

    def test_women_fev1_is_not_the_sitting_height_equation(self):
        # Sitting-height variant: 0.051 (sitting height) - 0.029 (age) - 0.55
        sitting = 0.051 * 160 - 0.029 * 35 - 0.55
        self.assertNotAlmostEqual(predicted(self.eq, F, 35, 160, FEV1), sitting, places=2)


class TestMokoetle1994Percent(unittest.TestCase):

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_measured_equal_to_predicted_is_100(self):
        pred = 0.053 * 170 - 0.021 * 35 - 3.85
        self.assertAlmostEqual(self.eq.percent(M, 35, 170, parameter=FVC, value=pred),
                               100.0, places=2)

    def test_women_measured_equal_to_predicted_is_100(self):
        pred = 0.034 * 160 - 0.028 * 35 - 1.87
        self.assertAlmostEqual(self.eq.percent(F, 35, 160, parameter=FEV1, value=pred),
                               100.0, places=2)

    def test_half_of_predicted_is_50(self):
        pred = 0.035 * 170 - 0.036 * 35 - 1.15
        self.assertAlmostEqual(self.eq.percent(M, 35, 170, parameter=FEV1, value=pred / 2),
                               50.0, places=2)

    def test_missing_value_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 35, 170, parameter=FVC)))


class TestMokoetle1994RaceNeutral(unittest.TestCase):
    """The cohort was entirely black South African, so there is no ethnicity term."""

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_ethnicity_is_ignored(self):
        base = self.eq.percent(M, 35, 170, parameter=FVC, value=4.0)
        for ethnicity in (0, 1, 2, None):
            self.assertEqual(
                self.eq.percent(M, 35, 170, ethnicity=ethnicity, parameter=FVC, value=4.0),
                base)


class TestMokoetle1994Ranges(unittest.TestCase):
    """Height bounds are mean +- 2 SD; the paper publishes no observed ranges."""

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_men_and_women_have_different_height_ranges(self):
        self.assertNotEqual(MOKOETLE_1994._HEIGHT_MALE_RANGE,
                            MOKOETLE_1994._HEIGHT_FEMALE_RANGE)

    def test_man_of_180cm_is_in_range(self):
        # 168.7 + 2*6.5 = 181.7, so 180 cm is within the fitted population.
        self.assertIsInstance(self.eq.percent(M, 40, 180, parameter=FVC, value=4.5), float)

    def test_woman_of_168cm_is_in_range(self):
        # 158.0 + 2*5.5 = 169.0
        self.assertIsInstance(self.eq.percent(F, 40, 168, parameter=FVC, value=3.5), float)

    def test_man_height_above_range_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 40, 190, parameter=FVC, value=5.0)))

    def test_man_height_below_range_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 40, 150, parameter=FVC, value=3.5)))

    def test_woman_height_above_range_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(F, 40, 175, parameter=FVC, value=4.0)))

    def test_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 18, 170, parameter=FVC, value=4.5)))

    def test_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 70, 170, parameter=FVC, value=3.5)))

    def test_closest_strategy_clamps_age(self):
        self.eq.set_strategy("closest")
        clamped = self.eq.percent(M, 80, 170, parameter=FVC, value=4.0)
        at_bound = self.eq.percent(M, 65, 170, parameter=FVC, value=4.0)
        self.assertAlmostEqual(clamped, at_bound, places=6)


class TestMokoetle1994UnavailableMetrics(unittest.TestCase):
    """No LLN was published, so lln/uln/zscore/lms return NA."""

    def setUp(self):
        self.eq = MOKOETLE_1994()

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.eq.zscore(M, 40, 170, parameter=FVC, value=4.2)))

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.eq.lln(M, 40, 170, parameter=FVC)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.eq.uln(M, 40, 170, parameter=FVC)))

    def test_lms_returns_na(self):
        l, m, s = self.eq.lms(M, 40, 170, parameter=FVC)
        self.assertTrue(pd.isna(l) and pd.isna(m) and pd.isna(s))


class TestMokoetle1994Compute(unittest.TestCase):

    def test_compute_dataframe(self):
        eq = MOKOETLE_1994()
        df = pd.DataFrame({
            'sex': [M, F],
            'age': [35, 35],
            'height': [170, 160],
            'FVC': [4.425, 3.355],
        })
        result = eq.compute(df, parameter=FVC, value_col='FVC', metrics=('percent',))
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result['percent'].iloc[0], 100.0, delta=0.01)
        self.assertAlmostEqual(result['percent'].iloc[1], 100.0, delta=0.01)


if __name__ == '__main__':
    unittest.main()

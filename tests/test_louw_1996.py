import unittest
import pandas as pd
from pyspiro import LOUW_1996

M = 1
F = 0

BLACK = 0
WHITE = 1

FVC = LOUW_1996.Parameters.FVC.value
FEV1 = LOUW_1996.Parameters.FEV1.value

AUTOLINK = LOUW_1996.Spirometer.AUTOLINK.value
VITALOGRAPH = LOUW_1996.Spirometer.VITALOGRAPH.value


def predicted(eq, sex, age, height, ethnicity, parameter):
    """Predicted value in litres. percent() rounds to 2 dp, so go via _compute()."""
    return eq._compute(sex, age, height, ethnicity, parameter)


class TestLouw1996Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(LOUW_1996())

    def test_default_spirometer_is_autolink(self):
        self.assertEqual(LOUW_1996()._spirometer, LOUW_1996.Spirometer.AUTOLINK)

    def test_parameters_enum(self):
        params = [p.name for p in LOUW_1996.Parameters]
        for name in ('FVC', 'FEV1'):
            self.assertIn(name, params)


class TestLouw1996TableV(unittest.TestCase):
    """FVC coefficients, Table V ('healthy' group, standing height)."""

    def test_vitalograph_black(self):
        # 0.048 height - 0.024 age - 3.08 (R2 = 0.33)
        eq = LOUW_1996(VITALOGRAPH)
        self.assertAlmostEqual(predicted(eq, M, 35, 170, BLACK, FVC), 4.240, places=3)

    def test_vitalograph_white(self):
        # 0.056 height - 0.031 age - 3.42 (R2 = 0.55)
        eq = LOUW_1996(VITALOGRAPH)
        self.assertAlmostEqual(predicted(eq, M, 40, 175, WHITE, FVC), 5.140, places=3)

    def test_autolink_black(self):
        # 0.053 height - 0.030 age - 3.54 (R2 = 0.38)
        eq = LOUW_1996(AUTOLINK)
        self.assertAlmostEqual(predicted(eq, M, 35, 170, BLACK, FVC), 4.420, places=3)

    def test_autolink_white(self):
        # 0.056 height - 0.038 age - 3.07 (R2 = 0.57)
        eq = LOUW_1996(AUTOLINK)
        self.assertAlmostEqual(predicted(eq, M, 40, 175, WHITE, FVC), 5.210, places=3)


class TestLouw1996TableVI(unittest.TestCase):
    """FEV1 coefficients, Table VI ('healthy' group, standing height)."""

    def test_vitalograph_black(self):
        # 0.029 height - 0.027 age - 0.535 (R2 = 0.35)
        eq = LOUW_1996(VITALOGRAPH)
        self.assertAlmostEqual(predicted(eq, M, 35, 170, BLACK, FEV1), 3.450, places=3)

    def test_vitalograph_white(self):
        # 0.042 height - 0.036 age - 1.84 (R2 = 0.25)
        eq = LOUW_1996(VITALOGRAPH)
        self.assertAlmostEqual(predicted(eq, M, 40, 175, WHITE, FEV1), 4.070, places=3)

    def test_autolink_black_uses_table_not_abstract(self):
        # Table VI gives 0.036 for the height term; the abstract prints 0.038.
        # 0.036*170 - 0.032*35 - 1.18 = 3.820  (abstract's 0.038 would give 4.160)
        eq = LOUW_1996(AUTOLINK)
        self.assertAlmostEqual(predicted(eq, M, 35, 170, BLACK, FEV1), 3.820, places=3)

    def test_autolink_white(self):
        # 0.042 height - 0.038 age - 1.45 (R2 = 0.27)
        eq = LOUW_1996(AUTOLINK)
        self.assertAlmostEqual(predicted(eq, M, 40, 175, WHITE, FEV1), 4.380, places=3)


class TestLouw1996ReproducesGroupMeans(unittest.TestCase):
    """An OLS fit with an intercept reproduces the group mean at the mean predictors.

    Healthy-group means, Table III: black 169.7 cm / 41.1 y, white 178.8 cm / 37.3 y.
    Observed lung function, Table IV.
    """

    def test_autolink_black_fvc(self):
        eq = LOUW_1996(AUTOLINK)
        pred = predicted(eq, M, 41.1, 169.7, BLACK, FVC)
        self.assertAlmostEqual(pred, 4.26, delta=0.06)  # Table IV: 4.26 +- 0.7

    def test_autolink_black_fev1(self):
        # The discriminating case: 0.036 lands on the observed mean, 0.038 misses by 0.38 L.
        eq = LOUW_1996(AUTOLINK)
        pred = predicted(eq, M, 41.1, 169.7, BLACK, FEV1)
        self.assertAlmostEqual(pred, 3.57, delta=0.06)  # Table IV: 3.57 +- 0.6

    def test_autolink_black_fev1_rejects_abstract_coefficient(self):
        eq = LOUW_1996(AUTOLINK)
        pred = predicted(eq, M, 41.1, 169.7, BLACK, FEV1)
        abstract_value = 0.038 * 169.7 - 0.032 * 41.1 - 1.18
        self.assertGreater(abs(abstract_value - 3.57), 0.3)
        self.assertLess(abs(pred - 3.57), 0.1)

    def test_autolink_white_fvc(self):
        eq = LOUW_1996(AUTOLINK)
        pred = predicted(eq, M, 37.3, 178.8, WHITE, FVC)
        self.assertAlmostEqual(pred, 5.57, delta=0.06)  # Table IV: 5.57 +- 0.8


class TestLouw1996DiscussionWorkedExample(unittest.TestCase):
    """Discussion: predicted FVC for a 40-year-old man of 170 cm."""

    def test_autolink_black(self):
        eq = LOUW_1996(AUTOLINK)
        self.assertAlmostEqual(predicted(eq, M, 40, 170, BLACK, FVC), 4.25, delta=0.03)

    def test_vitalograph_black(self):
        eq = LOUW_1996(VITALOGRAPH)
        self.assertAlmostEqual(predicted(eq, M, 40, 170, BLACK, FVC), 4.13, delta=0.03)

    def test_vitalograph_white(self):
        eq = LOUW_1996(VITALOGRAPH)
        self.assertAlmostEqual(predicted(eq, M, 40, 170, WHITE, FVC), 4.83, delta=0.04)


class TestLouw1996Percent(unittest.TestCase):

    def setUp(self):
        self.eq = LOUW_1996(AUTOLINK)

    def test_measured_equal_to_predicted_is_100(self):
        pred = 0.053 * 170 - 0.030 * 35 - 3.54
        result = self.eq.percent(M, 35, 170, ethnicity=BLACK, parameter=FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_half_of_predicted_is_50(self):
        pred = 0.053 * 170 - 0.030 * 35 - 3.54
        result = self.eq.percent(M, 35, 170, ethnicity=BLACK, parameter=FVC, value=pred / 2)
        self.assertAlmostEqual(result, 50.0, places=2)

    def test_missing_ethnicity_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 35, 170, parameter=FVC, value=4.0)))

    def test_missing_parameter_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 35, 170, ethnicity=BLACK, value=4.0)))

    def test_missing_value_returns_na(self):
        self.assertTrue(pd.isna(self.eq.percent(M, 35, 170, ethnicity=BLACK, parameter=FVC)))

    def test_invalid_ethnicity_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 35, 170, ethnicity=2, parameter=FVC, value=4.0)))


class TestLouw1996MenOnly(unittest.TestCase):
    """Louw 1996 studied men only; women must not silently get a men's prediction."""

    def setUp(self):
        self.eq = LOUW_1996(AUTOLINK)

    def test_female_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(F, 35, 165, ethnicity=BLACK, parameter=FVC, value=3.5)))

    def test_male_returns_value(self):
        self.assertIsInstance(
            self.eq.percent(M, 35, 170, ethnicity=BLACK, parameter=FVC, value=4.4), float)


class TestLouw1996Ranges(unittest.TestCase):
    """Height bounds are the observed Table III ranges of the healthy group."""

    def setUp(self):
        self.eq = LOUW_1996(AUTOLINK)

    def test_white_range_is_not_the_black_range(self):
        self.assertNotEqual(LOUW_1996._HEIGHT_BLACK_RANGE, LOUW_1996._HEIGHT_WHITE_RANGE)

    def test_white_mean_height_is_in_range(self):
        # The healthy white group's mean standing height is 178.8 cm (Table III).
        self.assertIsInstance(
            self.eq.percent(M, 37, 178.8, ethnicity=WHITE, parameter=FVC, value=5.5), float)

    def test_tall_white_man_in_range(self):
        # Table III white standing height range: 163-206 cm.
        self.assertIsInstance(
            self.eq.percent(M, 40, 195, ethnicity=WHITE, parameter=FVC, value=6.0), float)

    def test_tall_black_man_in_range(self):
        # Table III black standing height range: 155-191 cm.
        self.assertIsInstance(
            self.eq.percent(M, 40, 188, ethnicity=BLACK, parameter=FVC, value=5.5), float)

    def test_black_height_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 40, 195, ethnicity=BLACK, parameter=FVC, value=5.5)))

    def test_white_height_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 40, 158, ethnicity=WHITE, parameter=FVC, value=4.0)))

    def test_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 18, 170, ethnicity=BLACK, parameter=FVC, value=4.5)))

    def test_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.eq.percent(M, 75, 170, ethnicity=BLACK, parameter=FVC, value=3.5)))

    def test_closest_strategy_clamps_height(self):
        self.eq.set_strategy("closest")
        clamped = self.eq.percent(M, 40, 200, ethnicity=BLACK, parameter=FVC, value=5.0)
        at_bound = self.eq.percent(M, 40, 191, ethnicity=BLACK, parameter=FVC, value=5.0)
        self.assertAlmostEqual(clamped, at_bound, places=6)


class TestLouw1996SpirometerSelection(unittest.TestCase):

    def test_autolink_and_vitalograph_differ(self):
        a = predicted(LOUW_1996(AUTOLINK), M, 40, 170, BLACK, FVC)
        v = predicted(LOUW_1996(VITALOGRAPH), M, 40, 170, BLACK, FVC)
        self.assertNotAlmostEqual(a, v, places=2)

    def test_autolink_reads_higher_fvc_than_vitalograph(self):
        # The paper reports the Autolink giving higher FVC values than the Vitalograph.
        a = predicted(LOUW_1996(AUTOLINK), M, 40, 170, BLACK, FVC)
        v = predicted(LOUW_1996(VITALOGRAPH), M, 40, 170, BLACK, FVC)
        self.assertGreater(a, v)


class TestLouw1996UnavailableMetrics(unittest.TestCase):
    """No LLN was published, so lln/uln/zscore/lms return NA."""

    def setUp(self):
        self.eq = LOUW_1996()

    def test_zscore_returns_na(self):
        self.assertTrue(pd.isna(self.eq.zscore(M, 40, 170, ethnicity=BLACK, parameter=FVC, value=4.2)))

    def test_lln_returns_na(self):
        self.assertTrue(pd.isna(self.eq.lln(M, 40, 170, ethnicity=BLACK, parameter=FVC)))

    def test_uln_returns_na(self):
        self.assertTrue(pd.isna(self.eq.uln(M, 40, 170, ethnicity=BLACK, parameter=FVC)))

    def test_lms_returns_na(self):
        l, m, s = self.eq.lms(M, 40, 170, ethnicity=BLACK, parameter=FVC)
        self.assertTrue(pd.isna(l) and pd.isna(m) and pd.isna(s))


class TestLouw1996Compute(unittest.TestCase):

    def test_compute_dataframe(self):
        eq = LOUW_1996(AUTOLINK)
        df = pd.DataFrame({
            'sex': [M, M],
            'age': [35, 40],
            'height': [170, 175],
            'ethnicity': [BLACK, WHITE],
            'FVC': [4.42, 5.21],
        })
        result = eq.compute(df, parameter=FVC, ethnicity_col='ethnicity',
                            value_col='FVC', metrics=('percent',))
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result['percent'].iloc[0], 100.0, delta=0.1)
        self.assertAlmostEqual(result['percent'].iloc[1], 100.0, delta=0.1)


if __name__ == '__main__':
    unittest.main()

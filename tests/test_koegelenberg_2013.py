import unittest
import pandas as pd
from pyspiro import KOEGELENBERG_2013, LOUW_1996, MOKOETLE_1994

BLACK_OR_ASIAN = 0
MIXED = 1

M = 1
F = 0

# ---------------------------------------------------------------------------
# van Rooyen Y, Huisman HW, Schutte AE, Eloff FC, Du Plessis JL, Kruger A,
# Van Rooyen JM. South African and International Reference Values for Lung
# Function and its Relationship with Blood Pressure in Africans.
# Heart Lung Circ 2015;24:573-582. DOI: 10.1016/j.hlc.2014.12.005
#
# Table 1, PURE study, 2010 black South Africans. Used here as an independent
# validation set: Rooyen applied the 0.9 SATS factor to Quanjer 1993 predictions,
# and derived its South African predictions from Louw 1996 and Mokoetle 1994.
#
# Note: the abstract reports the highest percentages of predicted "for FEV1 and FVC
# (87.9 and 99.7%, respectively)". Those are in fact the men's and the women's FEV1%.
# Table 1, reproduced below, is authoritative.
# ---------------------------------------------------------------------------
PURE = {
    'men': {
        'n': 746,
        'age_mean': 50.3, 'age_sd': 10.3,
        'height_mean': 167.0, 'height_sd': 7.0,   # Table 1 gives 1.67 +- 0.07 m
        'fev1_mean': 2.62, 'fev1_sd': 0.76,
        'fvc_mean': 3.14, 'fvc_sd': 0.84,
        'fev1_fvc_ratio': 83.7,
        # European (Quanjer 1993), uncorrected predicted and after the 0.9 factor
        'fev1_pred_eur': 3.26, 'fev1_pred_eur_corrected': 2.93,
        'fvc_pred_eur': 4.01, 'fvc_pred_eur_corrected': 3.61,
        # South African (Louw 1996), predicted and % predicted
        'fev1_pred_sa': 2.96, 'fev1_pct_sa': 87.9,
        'fvc_pred_sa': 3.76, 'fvc_pct_sa': 83.0,
    },
    'women': {
        'n': 1264,
        'age_mean': 49.6, 'age_sd': 10.4,
        'height_mean': 157.0, 'height_sd': 6.0,   # Table 1 gives 1.57 +- 0.06 m
        'fev1_mean': 2.04, 'fev1_sd': 0.54,
        'fvc_mean': 2.37, 'fvc_sd': 0.62,
        'fev1_fvc_ratio': 86.8,
        'fev1_pred_eur': 2.35, 'fev1_pred_eur_corrected': 2.12,
        'fvc_pred_eur': 2.76, 'fvc_pred_eur_corrected': 2.49,
        # South African (Mokoetle 1994), predicted and % predicted
        'fev1_pred_sa': 2.07, 'fev1_pct_sa': 99.7,
        'fvc_pred_sa': 2.87, 'fvc_pct_sa': 82.4,
    },
}


class TestKoegelenberg2013Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(KOEGELENBERG_2013())

    def test_is_not_a_reference_equation(self):
        # It carries no prediction equation, so it must not pretend to be a Reference.
        from pyspiro.src.reference import Reference
        self.assertNotIsInstance(KOEGELENBERG_2013(), Reference)

    def test_ethnicity_enum(self):
        codes = {e.name: e.value for e in KOEGELENBERG_2013.Ethnicity}
        self.assertEqual(codes, {'BLACK_OR_ASIAN': 0, 'MIXED': 1})


class TestKoegelenberg2013Factors(unittest.TestCase):
    """SATS proposes 0.9 for black and Asian individuals, 0.95 for mixed ethnicity."""

    def setUp(self):
        self.eq = KOEGELENBERG_2013()

    def test_black_or_asian_constant(self):
        self.assertEqual(KOEGELENBERG_2013.BLACK_OR_ASIAN, 0.9)

    def test_mixed_constant(self):
        self.assertEqual(KOEGELENBERG_2013.MIXED_ETHNICITY, 0.95)

    def test_get_black_or_asian(self):
        self.assertEqual(self.eq.get_correction_factor(BLACK_OR_ASIAN), 0.9)

    def test_get_mixed(self):
        self.assertEqual(self.eq.get_correction_factor(MIXED), 0.95)

    def test_unknown_ethnicity_returns_na(self):
        self.assertTrue(pd.isna(self.eq.get_correction_factor(2)))

    def test_none_ethnicity_returns_na(self):
        self.assertTrue(pd.isna(self.eq.get_correction_factor(None)))


class TestKoegelenberg2013Correct(unittest.TestCase):

    def setUp(self):
        self.eq = KOEGELENBERG_2013()

    def test_published_worked_example(self):
        # "in a 45-year-old Asian male with a predicted FEV1 of 3 l (according to ECSC
        # predictions) the value would be corrected to 2.7 l (3.0 x 0.9)"
        self.assertAlmostEqual(self.eq.correct(3.0, BLACK_OR_ASIAN), 2.7, places=6)

    def test_mixed_ethnicity(self):
        self.assertAlmostEqual(self.eq.correct(3.0, MIXED), 2.85, places=6)

    def test_correction_lowers_the_predicted_value(self):
        for ethnicity in (BLACK_OR_ASIAN, MIXED):
            self.assertLess(self.eq.correct(4.0, ethnicity), 4.0)

    def test_unknown_ethnicity_returns_na(self):
        self.assertTrue(pd.isna(self.eq.correct(3.0, 2)))

    def test_missing_predicted_returns_na(self):
        self.assertTrue(pd.isna(self.eq.correct(None, BLACK_OR_ASIAN)))

    def test_na_predicted_returns_na(self):
        self.assertTrue(pd.isna(self.eq.correct(pd.NA, BLACK_OR_ASIAN)))


class TestKoegelenberg2013AgainstRooyenTable1(unittest.TestCase):
    """Rooyen 2015 applied the 0.9 factor to Quanjer 1993; Table 1 reports both rows.

    Table 1 prints predicted values to two decimals, so 0.9 x predicted can miss the
    printed corrected value by up to about 0.01 L.
    """

    def setUp(self):
        self.eq = KOEGELENBERG_2013()

    def test_men_fev1(self):
        d = PURE['men']
        self.assertAlmostEqual(self.eq.correct(d['fev1_pred_eur'], BLACK_OR_ASIAN),
                               d['fev1_pred_eur_corrected'], delta=0.01)

    def test_men_fvc(self):
        d = PURE['men']
        self.assertAlmostEqual(self.eq.correct(d['fvc_pred_eur'], BLACK_OR_ASIAN),
                               d['fvc_pred_eur_corrected'], delta=0.01)

    def test_women_fev1(self):
        d = PURE['women']
        self.assertAlmostEqual(self.eq.correct(d['fev1_pred_eur'], BLACK_OR_ASIAN),
                               d['fev1_pred_eur_corrected'], delta=0.01)

    def test_women_fvc(self):
        d = PURE['women']
        self.assertAlmostEqual(self.eq.correct(d['fvc_pred_eur'], BLACK_OR_ASIAN),
                               d['fvc_pred_eur_corrected'], delta=0.01)

    def test_the_mixed_factor_does_not_reproduce_table_1(self):
        # Rooyen studied black South Africans, so 0.95 must not fit the correction rows.
        d = PURE['men']
        self.assertNotAlmostEqual(self.eq.correct(d['fvc_pred_eur'], MIXED),
                                  d['fvc_pred_eur_corrected'], places=2)


class TestRooyenTable1CrossValidatesSouthAfricanEquations(unittest.TestCase):
    """Rooyen derived its South African predicted values from Louw 1996 and Mokoetle 1994.

    Both are linear in height and age, so the mean of the individual predictions equals
    the prediction at the mean height and age. Table 1's 'South African predicted value'
    rows are therefore a check on those two modules from an independent publication.

    The men's values match Louw's Vitalograph black equations, not the Autolink ones.
    """

    def test_women_fev1_matches_mokoetle(self):
        d = PURE['women']
        eq = MOKOETLE_1994()
        pred = eq._compute(F, d['age_mean'], d['height_mean'],
                           MOKOETLE_1994.Parameters.FEV1.value)
        self.assertAlmostEqual(pred, d['fev1_pred_sa'], delta=0.02)

    def test_women_fvc_matches_mokoetle(self):
        d = PURE['women']
        eq = MOKOETLE_1994()
        pred = eq._compute(F, d['age_mean'], d['height_mean'],
                           MOKOETLE_1994.Parameters.FVC.value)
        self.assertAlmostEqual(pred, d['fvc_pred_sa'], delta=0.02)

    def test_men_fev1_matches_louw_vitalograph(self):
        d = PURE['men']
        eq = LOUW_1996(LOUW_1996.Spirometer.VITALOGRAPH.value)
        pred = eq._compute(M, d['age_mean'], d['height_mean'], 0,
                           LOUW_1996.Parameters.FEV1.value)
        self.assertAlmostEqual(pred, d['fev1_pred_sa'], delta=0.02)

    def test_men_fvc_matches_louw_vitalograph(self):
        d = PURE['men']
        eq = LOUW_1996(LOUW_1996.Spirometer.VITALOGRAPH.value)
        pred = eq._compute(M, d['age_mean'], d['height_mean'], 0,
                           LOUW_1996.Parameters.FVC.value)
        self.assertAlmostEqual(pred, d['fvc_pred_sa'], delta=0.04)


class TestRooyenTable1Consistency(unittest.TestCase):
    """Internal consistency of the Table 1 figures reproduced in this file."""

    def test_percent_predicted_follows_from_measured_over_predicted(self):
        # Ratio of means, so a little slack against the published mean of ratios.
        for sex in ('men', 'women'):
            d = PURE[sex]
            for p in ('fev1', 'fvc'):
                pct = d['%s_mean' % p] / d['%s_pred_sa' % p] * 100
                self.assertAlmostEqual(pct, d['%s_pct_sa' % p], delta=1.5)

    def test_fev1_fvc_ratio_follows_from_means(self):
        for sex, lo, hi in (('men', 80, 85), ('women', 85, 87)):
            d = PURE[sex]
            self.assertTrue(lo <= d['fev1_mean'] / d['fvc_mean'] * 100 <= hi)

    def test_fvc_percent_predicted_is_not_the_abstract_figure(self):
        # The abstract's "99.7%" for FVC is the women's FEV1%, not an FVC figure.
        self.assertNotAlmostEqual(PURE['men']['fvc_pct_sa'], 99.7, places=1)
        self.assertNotAlmostEqual(PURE['women']['fvc_pct_sa'], 99.7, places=1)
        self.assertAlmostEqual(PURE['women']['fev1_pct_sa'], 99.7, places=1)


if __name__ == '__main__':
    unittest.main()

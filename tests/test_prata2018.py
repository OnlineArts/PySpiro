import math
import unittest

import pandas as pd

from pyspiro import PRATA_2018, PEREIRA_2007

M = 1
F = 0

# Representative covariates: median height and mean age of each sex in the
# Prata cohort (Table 1). Used to reproduce the Table 2 means.
MALE_HT, MALE_AGE = 171.0, 45.0
FEMALE_HT, FEMALE_AGE = 158.0, 47.0


class TestPrata2018Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(PRATA_2018())

    def test_age_ranges(self):
        # Table 3/4 headers: males 26-82 y, females 20-83 y.
        p = PRATA_2018()
        self.assertEqual(p._AGE_RANGE_MALE, (26, 82))
        self.assertEqual(p._AGE_RANGE_FEMALE, (20, 83))

    def test_height_ranges(self):
        # Results: males 151-187 cm, females 145-175 cm.
        p = PRATA_2018()
        self.assertEqual(p._HEIGHT_RANGE_MALE, (151.0, 187.0))
        self.assertEqual(p._HEIGHT_RANGE_FEMALE, (145.0, 175.0))

    def test_parameters_enum(self):
        params = [p.name for p in PRATA_2018.Parameters]
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'PEF', 'FEF25_75', 'FEF50', 'FEF75'):
            self.assertIn(name, params)

    def test_coefficients_loaded_for_both_sexes(self):
        p = PRATA_2018()
        self.assertEqual(len(p._coefficients), 14)  # 7 parameters x 2 sexes
        for name in ('FVC', 'FEV1', 'FEV1FVC', 'PEF', 'FEF25_75', 'FEF50', 'FEF75'):
            for sex in ('male', 'female'):
                self.assertIn((name, sex), p._coefficients.index)

    def test_coefficients_have_no_missing_values(self):
        p = PRATA_2018()
        self.assertFalse(p._coefficients.isna().any().any())

    def test_flows_are_log_volumes_are_linear(self):
        p = PRATA_2018()
        for sex in ('male', 'female'):
            for name in ('FVC', 'FEV1', 'FEV1FVC', 'PEF'):
                self.assertEqual(p._coefficients.loc[(name, sex), 'kind'], 'linear')
            for name in ('FEF25_75', 'FEF50', 'FEF75'):
                self.assertEqual(p._coefficients.loc[(name, sex), 'kind'], 'log')


class TestPrata2018Percent(unittest.TestCase):
    """Values re-derived from the coefficients printed in Tables 3 and 4."""

    def setUp(self):
        self.p = PRATA_2018()

    def test_male_fvc_at_predicted_is_100(self):
        # Table 3 footnote worked example: FVC = height x 0.048 - age x 0.019 - 2.931
        pred = 0.048 * 171 - 0.019 * 45 - 2.931
        result = self.p.percent(M, 45, 171, parameter=PRATA_2018.Parameters.FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev1_at_predicted_is_100(self):
        pred = 0.033 * 171 - 0.024 * 45 - 0.989
        result = self.p.percent(M, 45, 171, parameter=PRATA_2018.Parameters.FEV1, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev1fvc_at_predicted_is_100(self):
        pred = -0.134 * 171 - 0.189 * 45 + 112.0
        result = self.p.percent(M, 45, 171, parameter=PRATA_2018.Parameters.FEV1FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_pef_at_predicted_is_100(self):
        pred = 0.059 * 171 - 0.048 * 45 + 1.903
        result = self.p.percent(M, 45, 171, parameter=PRATA_2018.Parameters.PEF, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fef25_75_footnote_worked_example(self):
        # Table 3 footnote: FEF25-75% = 2.7183^(-ln(age) x 0.670 + 3.735)
        pred = math.exp(-0.670 * math.log(45) + 3.735)
        result = self.p.percent(M, 45, 171, parameter=PRATA_2018.Parameters.FEF25_75, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fvc_at_predicted_is_100(self):
        pred = 0.035 * 158 - 0.013 * 47 - 1.83
        result = self.p.percent(F, 47, 158, parameter=PRATA_2018.Parameters.FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fev1_at_predicted_is_100(self):
        pred = 0.025 * 158 - 0.017 * 47 - 0.69
        result = self.p.percent(F, 47, 158, parameter=PRATA_2018.Parameters.FEV1, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fef75_log_at_predicted_is_100(self):
        pred = math.exp(-1.01 * math.log(47) + 3.805)
        result = self.p.percent(F, 47, 158, parameter=PRATA_2018.Parameters.FEF75, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_flows_carry_no_height_term(self):
        # Table 3 prints "-" in the height column for all three log equations.
        for name in ('FEF25_75', 'FEF50', 'FEF75'):
            param = PRATA_2018.Parameters[name]
            short = self.p.percent(M, 45, 155, parameter=param, value=3.0)
            tall = self.p.percent(M, 45, 185, parameter=param, value=3.0)
            self.assertEqual(short, tall, msg=name)

    def test_female_pef_carries_no_height_term(self):
        # Table 4 prints "-" in the height column for PEF; male PEF does use height.
        short = self.p.percent(F, 47, 148, parameter=PRATA_2018.Parameters.PEF, value=6.7)
        tall = self.p.percent(F, 47, 172, parameter=PRATA_2018.Parameters.PEF, value=6.7)
        self.assertEqual(short, tall)

    def test_male_pef_does_depend_on_height(self):
        short = self.p.percent(M, 45, 155, parameter=PRATA_2018.Parameters.PEF, value=9.8)
        tall = self.p.percent(M, 45, 185, parameter=PRATA_2018.Parameters.PEF, value=9.8)
        self.assertNotEqual(short, tall)

    def test_unknown_parameter_raises(self):
        with self.assertRaises(ValueError):
            self.p.percent(M, 45, 171, parameter=99, value=4.0)


class TestPrata2018TableTwoMeans(unittest.TestCase):
    """The linear equations should reproduce the Table 2 means at the cohort's
    median height and mean age. Log equations predict the geometric mean and so
    run below the reported arithmetic mean; only their direction is checked."""

    def setUp(self):
        self.p = PRATA_2018()

    def test_male_linear_means(self):
        for name, observed in (('FVC', 4.42), ('FEV1', 3.55), ('FEV1FVC', 80.3), ('PEF', 9.77)):
            pct = self.p.percent(M, MALE_AGE, MALE_HT,
                                 parameter=PRATA_2018.Parameters[name], value=observed)
            self.assertAlmostEqual(pct, 100.0, delta=2.0, msg=name)

    def test_female_linear_means(self):
        for name, observed in (('FVC', 3.10), ('FEV1', 2.55), ('FEV1FVC', 82.0), ('PEF', 6.73)):
            pct = self.p.percent(F, FEMALE_AGE, FEMALE_HT,
                                 parameter=PRATA_2018.Parameters[name], value=observed)
            self.assertAlmostEqual(pct, 100.0, delta=4.0, msg=name)

    def test_log_flows_predict_geometric_mean_below_arithmetic_mean(self):
        for name, observed in (('FEF25_75', 3.54), ('FEF50', 4.39), ('FEF75', 1.43)):
            pct = self.p.percent(M, MALE_AGE, MALE_HT,
                                 parameter=PRATA_2018.Parameters[name], value=observed)
            self.assertGreater(pct, 100.0, msg=name)
            self.assertLess(pct, 125.0, msg=name)


class TestPrata2018LLN(unittest.TestCase):
    """Lower limits are the published 5th percentile of the residuals."""

    def setUp(self):
        self.p = PRATA_2018()

    def test_male_fvc_lln_is_predicted_minus_offset(self):
        pred = 0.048 * 171 - 0.019 * 45 - 2.931
        lln = self.p.lln(M, 45, 171, parameter=PRATA_2018.Parameters.FVC)
        self.assertAlmostEqual(lln, pred - 0.78, places=6)

    def test_male_fev1_lln_offset(self):
        pred = 0.033 * 171 - 0.024 * 45 - 0.989
        lln = self.p.lln(M, 45, 171, parameter=PRATA_2018.Parameters.FEV1)
        self.assertAlmostEqual(lln, pred - 0.76, places=6)

    def test_male_pef_lln_offset(self):
        pred = 0.059 * 171 - 0.048 * 45 + 1.903
        lln = self.p.lln(M, 45, 171, parameter=PRATA_2018.Parameters.PEF)
        self.assertAlmostEqual(lln, pred - 2.67, places=6)

    def test_female_fvc_lln_offset(self):
        pred = 0.035 * 158 - 0.013 * 47 - 1.83
        lln = self.p.lln(F, 47, 158, parameter=PRATA_2018.Parameters.FVC)
        self.assertAlmostEqual(lln, pred - 0.66, places=6)

    def test_female_fev1_lln_offset(self):
        pred = 0.025 * 158 - 0.017 * 47 - 0.69
        lln = self.p.lln(F, 47, 158, parameter=PRATA_2018.Parameters.FEV1)
        self.assertAlmostEqual(lln, pred - 0.55, places=6)

    def test_female_pef_lln_offset(self):
        pred = -0.029 * 47 + 8.134
        lln = self.p.lln(F, 47, 158, parameter=PRATA_2018.Parameters.PEF)
        self.assertAlmostEqual(lln, pred - 1.77, places=6)

    def test_male_log_flow_lln_is_multiplicative(self):
        # (age coefficient, constant, LLN factor) from Table 3.
        for name, c_age, const, factor in (('FEF25_75', -0.670, 3.735, 0.62),
                                           ('FEF50', -0.517, 3.383, 0.62),
                                           ('FEF75', -0.956, 3.872, 0.57)):
            pred = math.exp(c_age * math.log(45) + const)
            lln = self.p.lln(M, 45, 171, parameter=PRATA_2018.Parameters[name])
            self.assertAlmostEqual(lln, pred * factor, places=6, msg=name)

    def test_female_log_flow_lln_is_multiplicative(self):
        # (age coefficient, constant, LLN factor) from Table 4.
        for name, c_age, const, factor in (('FEF25_75', -0.625, 3.32, 0.63),
                                           ('FEF50', -0.436, 2.862, 0.61),
                                           ('FEF75', -1.01, 3.805, 0.54)):
            pred = math.exp(c_age * math.log(47) + const)
            lln = self.p.lln(F, 47, 158, parameter=PRATA_2018.Parameters[name])
            self.assertAlmostEqual(lln, pred * factor, places=6, msg=name)

    def test_fev1fvc_lln_uses_table_offsets_not_rounded_text_offsets(self):
        # Tables 3/4 give 8.70 (M) and 7.8 (F); the Results text rounds to 9 and 8.
        pred_m = -0.134 * 171 - 0.189 * 45 + 112.0
        self.assertAlmostEqual(
            self.p.lln(M, 45, 171, parameter=PRATA_2018.Parameters.FEV1FVC),
            pred_m - 8.70, places=6)
        pred_f = -0.074 * 158 - 0.200 * 47 + 103.2
        self.assertAlmostEqual(
            self.p.lln(F, 47, 158, parameter=PRATA_2018.Parameters.FEV1FVC),
            pred_f - 7.8, places=6)

    def test_lln_is_below_predicted(self):
        # A measurement sitting exactly on the LLN must score below 100% predicted.
        for sex, age, ht in ((M, 45, 171), (F, 47, 158)):
            for name in ('FVC', 'FEV1', 'FEV1FVC', 'PEF', 'FEF25_75', 'FEF50', 'FEF75'):
                param = PRATA_2018.Parameters[name]
                lln = self.p.lln(sex, age, ht, parameter=param)
                pct = self.p.percent(sex, age, ht, parameter=param, value=lln)
                self.assertLess(pct, 100.0, msg=name)


class TestPrata2018ManuscriptClaims(unittest.TestCase):

    def setUp(self):
        self.p = PRATA_2018()

    def test_male_fev1_declines_24_ml_per_year(self):
        # Results: "FEV1 decreased on average 24 mL per year in males".
        a = self.p.lln(M, 45, 171, parameter=PRATA_2018.Parameters.FEV1)
        b = self.p.lln(M, 46, 171, parameter=PRATA_2018.Parameters.FEV1)
        self.assertAlmostEqual((a - b) * 1000, 24.0, places=6)

    def test_female_fev1_declines_17_ml_per_year(self):
        # Results: "...and 17 mL per year in females".
        a = self.p.lln(F, 47, 158, parameter=PRATA_2018.Parameters.FEV1)
        b = self.p.lln(F, 48, 158, parameter=PRATA_2018.Parameters.FEV1)
        self.assertAlmostEqual((a - b) * 1000, 17.0, places=6)

    def test_height_negatively_influences_fev1fvc(self):
        short = self.p.lln(M, 45, 155, parameter=PRATA_2018.Parameters.FEV1FVC)
        tall = self.p.lln(M, 45, 185, parameter=PRATA_2018.Parameters.FEV1FVC)
        self.assertLess(tall, short)


class TestPrata2018Unavailable(unittest.TestCase):
    """No SEE or residual SD was published."""

    def setUp(self):
        self.p = PRATA_2018()

    def test_zscore_is_na(self):
        self.assertTrue(pd.isna(
            self.p.zscore(M, 45, 171, parameter=PRATA_2018.Parameters.FVC, value=4.4)))

    def test_uln_is_na(self):
        self.assertTrue(pd.isna(self.p.uln(M, 45, 171, parameter=PRATA_2018.Parameters.FVC)))

    def test_lms_is_na_triple(self):
        l, m, s = self.p.lms(M, 45, 171, parameter=PRATA_2018.Parameters.FVC)
        self.assertTrue(pd.isna(l) and pd.isna(m) and pd.isna(s))


class TestPrata2018OutOfRange(unittest.TestCase):

    def setUp(self):
        self.p = PRATA_2018()

    def test_male_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(M, 25, 171, parameter=PRATA_2018.Parameters.FVC, value=4.4)))

    def test_male_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(M, 83, 171, parameter=PRATA_2018.Parameters.FVC, value=4.4)))

    def test_female_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(F, 19, 158, parameter=PRATA_2018.Parameters.FVC, value=3.1)))

    def test_female_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(F, 84, 158, parameter=PRATA_2018.Parameters.FVC, value=3.1)))

    def test_male_height_out_of_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(M, 45, 150, parameter=PRATA_2018.Parameters.FVC, value=4.4)))
        self.assertTrue(pd.isna(
            self.p.percent(M, 45, 188, parameter=PRATA_2018.Parameters.FVC, value=4.4)))

    def test_female_height_out_of_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(F, 47, 144, parameter=PRATA_2018.Parameters.FVC, value=3.1)))
        self.assertTrue(pd.isna(
            self.p.percent(F, 47, 176, parameter=PRATA_2018.Parameters.FVC, value=3.1)))

    def test_lln_out_of_range_returns_na(self):
        self.assertTrue(pd.isna(self.p.lln(M, 25, 171, parameter=PRATA_2018.Parameters.FVC)))

    def test_closest_strategy_clamps_age_to_boundary(self):
        self.p.set_strategy('closest')
        clamped = self.p.percent(M, 20, 171, parameter=PRATA_2018.Parameters.FVC, value=4.4)
        at_bound = self.p.percent(M, 26, 171, parameter=PRATA_2018.Parameters.FVC, value=4.4)
        self.assertEqual(clamped, at_bound)


class TestPrata2018Compute(unittest.TestCase):

    def setUp(self):
        self.p = PRATA_2018()
        self.df = pd.DataFrame({
            'sex': [M, F],
            'age': [45.0, 47.0],
            'height': [171.0, 158.0],
            'FVC': [4.42, 3.10],
        })

    def test_compute_needs_no_weight_column(self):
        # Weight played no role in any Prata equation, so it is absent from the API.
        out = self.p.compute(self.df, PRATA_2018.Parameters.FVC, value_col='FVC')
        self.assertEqual(len(out), 2)
        self.assertIn('percent', out.columns)

    def test_compute_percent_matches_scalar_call(self):
        out = self.p.compute(self.df, PRATA_2018.Parameters.FVC,
                             value_col='FVC', metrics=('percent',))
        scalar = self.p.percent(M, 45.0, 171.0, parameter=PRATA_2018.Parameters.FVC, value=4.42)
        self.assertAlmostEqual(out['percent'].iloc[0], scalar, places=6)

    def test_compute_lln_matches_scalar_call(self):
        out = self.p.compute(self.df, PRATA_2018.Parameters.FVC, metrics=('lln',))
        scalar = self.p.lln(F, 47.0, 158.0, parameter=PRATA_2018.Parameters.FVC)
        self.assertAlmostEqual(out['lln'].iloc[1], scalar, places=6)

    def test_compute_percent_without_value_col_raises(self):
        with self.assertRaises(ValueError):
            self.p.compute(self.df, PRATA_2018.Parameters.FVC, metrics=('percent',))


class TestBrazilianEquationsAgree(unittest.TestCase):
    """Prata 2018 (Black adults) against its companion Pereira 2007 (White adults).

    The paper's central claim is that predicted FVC and FEV1 are lower in Black
    Brazilian adults. The reported gaps are cohort means over each subject's own
    covariates, so a single-point evaluation reproduces the male figures closely
    but not the female FEV1 gap; only direction is asserted for the latter.
    """

    def setUp(self):
        self.prata = PRATA_2018()
        self.pereira = PEREIRA_2007()

    @staticmethod
    def _pred(eq, sex, age, ht, name, lln_offset):
        """Recover the predicted value exactly, as lln() + the published offset.

        percent() rounds to two decimals, so inverting it would lose ~0.01 L.
        """
        return eq.lln(sex, age, ht, parameter=type(eq).Parameters[name]) + lln_offset

    def test_male_fvc_gap_is_about_0_30_litres(self):
        # Results: "In males, FVC was on average 0.30 L lower in Black individuals".
        gap = (self._pred(self.pereira, M, 48, 171, 'FVC', 0.90)
               - self._pred(self.prata, M, 48, 171, 'FVC', 0.78))
        self.assertAlmostEqual(gap, 0.30, delta=0.02)

    def test_male_fev1_gap_is_about_0_28_litres(self):
        # Results: "...FEV1 being 0.28 L lower in the former than in the latter".
        gap = (self._pred(self.pereira, M, 48, 171, 'FEV1', 0.76)
               - self._pred(self.prata, M, 48, 171, 'FEV1', 0.76))
        self.assertAlmostEqual(gap, 0.28, delta=0.02)

    def test_prata_predicts_lower_volumes_than_pereira_in_both_sexes(self):
        # A fixed measurement scores a higher %predicted against the lower
        # (Prata) reference, in both sexes and for both volumes.
        for sex, age, ht, value in ((M, 48, 171, 4.0), (F, 50, 158, 2.8)):
            for name in ('FVC', 'FEV1'):
                prata_pct = self.prata.percent(
                    sex, age, ht, parameter=PRATA_2018.Parameters[name], value=value)
                pereira_pct = self.pereira.percent(
                    sex, age, ht, parameter=PEREIRA_2007.Parameters[name], value=value)
                self.assertGreater(prata_pct, pereira_pct, msg=f'{name} sex={sex}')


if __name__ == '__main__':
    unittest.main()

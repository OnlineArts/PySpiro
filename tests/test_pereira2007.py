import math
import unittest

import pandas as pd

from pyspiro import PEREIRA_2007

M = 1
F = 0

# Representative covariates: median height and mean age of each sex in the
# Pereira cohort (Table 1). Used to reproduce the Table 2 means.
MALE_HT, MALE_AGE, MALE_WT = 171.0, 48.0, 78.0
FEMALE_HT, FEMALE_AGE = 158.0, 50.0

ALL_PARAMS = ('FVC', 'FEV6', 'FEV1', 'FVC_WT', 'FEV6_WT', 'FEV1_WT',
              'FEV1FVC', 'FEV1FEV6', 'PEF', 'FEF50', 'FEF75', 'FEF25_75',
              'FEF75_85', 'FEF50_FVC', 'FEF75_FVC', 'FEF25_75_FVC', 'FEF75_85_FVC')


class TestPereira2007Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(PEREIRA_2007())

    def test_age_ranges(self):
        # Table 3/4 headers: males 26-86 y, females 20-85 y.
        p = PEREIRA_2007()
        self.assertEqual(p._AGE_RANGE_MALE, (26, 86))
        self.assertEqual(p._AGE_RANGE_FEMALE, (20, 85))

    def test_height_ranges(self):
        # Table 3/4 headers: males 152-192 cm, females 137-182 cm.
        p = PEREIRA_2007()
        self.assertEqual(p._HEIGHT_RANGE_MALE, (152.0, 192.0))
        self.assertEqual(p._HEIGHT_RANGE_FEMALE, (137.0, 182.0))

    def test_parameters_enum(self):
        params = [p.name for p in PEREIRA_2007.Parameters]
        for name in ALL_PARAMS:
            self.assertIn(name, params)

    def test_coefficients_loaded(self):
        # 17 male rows + 14 female rows (females have no weight equations).
        p = PEREIRA_2007()
        self.assertEqual(len(p._coefficients), 31)

    def test_coefficients_have_no_missing_values(self):
        p = PEREIRA_2007()
        self.assertFalse(p._coefficients.isna().any().any())

    def test_female_half_has_no_weight_equations(self):
        # "Weight influenced predicted FVC, FEV1 and FEV6 values in males, but
        # not in females" - so those rows were never derived.
        p = PEREIRA_2007()
        for name in ('FVC_WT', 'FEV6_WT', 'FEV1_WT'):
            self.assertIn((name, 'male'), p._coefficients.index)
            self.assertNotIn((name, 'female'), p._coefficients.index)

    def test_volumes_linear_flows_log(self):
        p = PEREIRA_2007()
        for name in ('FVC', 'FEV6', 'FEV1', 'FEV1FVC', 'FEV1FEV6'):
            self.assertEqual(p._coefficients.loc[(name, 'male'), 'kind'], 'linear')
        for name in ('PEF', 'FEF50', 'FEF75', 'FEF25_75', 'FEF75_85',
                     'FEF50_FVC', 'FEF75_FVC', 'FEF25_75_FVC', 'FEF75_85_FVC'):
            self.assertEqual(p._coefficients.loc[(name, 'male'), 'kind'], 'log')


class TestPereira2007Percent(unittest.TestCase):
    """Values re-derived from the coefficients printed in Tables 3 and 4."""

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_male_fvc_at_predicted_is_100(self):
        pred = 0.0517 * 171 - 0.0207 * 48 - 3.18
        result = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev6_at_predicted_is_100(self):
        pred = 0.0521 * 171 - 0.0229 * 48 - 3.179
        result = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FEV6, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev1_at_predicted_is_100(self):
        pred = 0.0338 * 171 - 0.0252 * 48 - 0.789
        result = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FEV1, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fvc_wt_footnote_worked_example(self):
        # Table 3 footnote: FVC = height x 0.0599 - age x 0.0213 - weight x 0.0106 - 3.748
        pred = 0.0599 * 171 - 0.0213 * 48 - 0.0106 * 78 - 3.748
        result = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC_WT,
                                value=pred, weight=78)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_pef_footnote_worked_example(self):
        # Table 3 footnote: PEF = 2.7183^(ln height x 0.83 - ln age x 0.114 - 1.432).
        # The table body prints the constant as -1.43, which is what the CSV carries.
        pred = math.exp(0.830 * math.log(171) - 0.114 * math.log(48) - 1.43)
        result = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.PEF, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fev1fvc_at_predicted_is_100(self):
        pred = -0.175 * 171 - 0.197 * 48 + 120.3
        result = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FEV1FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_fef50_fvc_ratio_at_predicted_is_100(self):
        pred = math.exp(-1.827 * math.log(171) - 0.307 * math.log(48) + 15.17)
        result = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FEF50_FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fvc_at_predicted_is_100(self):
        pred = 0.0441 * 158 - 0.0189 * 50 - 2.848
        result = self.p.percent(F, 50, 158, parameter=PEREIRA_2007.Parameters.FVC, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_fev1_at_predicted_is_100(self):
        pred = 0.0314 * 158 - 0.0203 * 50 - 1.353
        result = self.p.percent(F, 50, 158, parameter=PEREIRA_2007.Parameters.FEV1, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_female_pef_log_at_predicted_is_100(self):
        pred = math.exp(1.442 * math.log(158) - 0.125 * math.log(50) - 4.863)
        result = self.p.percent(F, 50, 158, parameter=PEREIRA_2007.Parameters.PEF, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)

    def test_male_flows_carry_no_height_term(self):
        # Table 3 prints "-" in the height column for FEF50/75/25-75/75-85.
        for name in ('FEF50', 'FEF75', 'FEF25_75', 'FEF75_85'):
            param = PEREIRA_2007.Parameters[name]
            short = self.p.percent(M, 48, 155, parameter=param, value=3.0)
            tall = self.p.percent(M, 48, 190, parameter=param, value=3.0)
            self.assertEqual(short, tall, msg=name)

    def test_female_flows_do_carry_a_height_term(self):
        # Table 4, unlike Table 3, prints height coefficients for every flow.
        for name in ('FEF50', 'FEF75', 'FEF25_75', 'FEF75_85'):
            param = PEREIRA_2007.Parameters[name]
            short = self.p.percent(F, 50, 145, parameter=param, value=3.0)
            tall = self.p.percent(F, 50, 175, parameter=param, value=3.0)
            self.assertNotEqual(short, tall, msg=name)

    def test_unknown_parameter_raises(self):
        with self.assertRaises(ValueError):
            self.p.percent(M, 48, 171, parameter=99, value=4.0)


class TestPereira2007TableTwoMeans(unittest.TestCase):
    """Linear equations reproduce the Table 2 arithmetic means. Log equations
    predict the geometric mean and so sit below the reported arithmetic mean."""

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_male_linear_means(self):
        for name, observed in (('FVC', 4.64), ('FEV6', 4.51), ('FEV1', 3.77),
                               ('FEV1FVC', 81.0), ('FEV1FEV6', 82.0)):
            pct = self.p.percent(M, MALE_AGE, MALE_HT,
                                 parameter=PEREIRA_2007.Parameters[name], value=observed)
            self.assertAlmostEqual(pct, 100.0, delta=3.0, msg=name)

    def test_female_linear_means(self):
        for name, observed in (('FVC', 3.14), ('FEV6', 3.11), ('FEV1', 2.56),
                               ('FEV1FVC', 81.0), ('FEV1FEV6', 82.0)):
            pct = self.p.percent(F, FEMALE_AGE, FEMALE_HT,
                                 parameter=PEREIRA_2007.Parameters[name], value=observed)
            self.assertAlmostEqual(pct, 100.0, delta=3.0, msg=name)

    def test_male_weight_equations_also_reproduce_means(self):
        for name, observed in (('FVC_WT', 4.64), ('FEV6_WT', 4.51), ('FEV1_WT', 3.77)):
            pct = self.p.percent(M, MALE_AGE, MALE_HT, parameter=PEREIRA_2007.Parameters[name],
                                 value=observed, weight=MALE_WT)
            self.assertAlmostEqual(pct, 100.0, delta=3.0, msg=name)

    def test_male_pef_reproduces_mean(self):
        pct = self.p.percent(M, MALE_AGE, MALE_HT,
                             parameter=PEREIRA_2007.Parameters.PEF, value=11.1)
        self.assertAlmostEqual(pct, 100.0, delta=3.0)

    def test_female_pef_reproduces_mean(self):
        pct = self.p.percent(F, FEMALE_AGE, FEMALE_HT,
                             parameter=PEREIRA_2007.Parameters.PEF, value=7.14)
        self.assertAlmostEqual(pct, 100.0, delta=3.0)

    def test_log_flows_sit_above_100_percent_at_arithmetic_mean(self):
        for sex, age, ht, means in (
                (M, MALE_AGE, MALE_HT,
                 (('FEF50', 4.82), ('FEF75', 1.58), ('FEF25_75', 3.87), ('FEF75_85', 1.02))),
                (F, FEMALE_AGE, FEMALE_HT,
                 (('FEF50', 3.40), ('FEF75', 1.07), ('FEF25_75', 2.70), ('FEF75_85', 0.71)))):
            for name, observed in means:
                pct = self.p.percent(sex, age, ht,
                                     parameter=PEREIRA_2007.Parameters[name], value=observed)
                self.assertGreater(pct, 100.0, msg=f'{name} sex={sex}')
                self.assertLess(pct, 130.0, msg=f'{name} sex={sex}')


class TestPereira2007FemaleFEF50Correction(unittest.TestCase):
    """Table 4 prints an age coefficient of -0.044 for female FEF50, which
    predicts ~15 L/s against a reported mean of 3.40 L/s. The CSV carries the
    reconstructed -0.444. This is the only coefficient that deviates from print."""

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_csv_carries_the_reconstructed_coefficient(self):
        self.assertAlmostEqual(
            float(self.p._coefficients.loc[('FEF50', 'female'), 'a_age']), -0.444, places=6)

    def test_predicted_is_physiologically_plausible(self):
        pred = math.exp(0.839 * math.log(158) - 0.444 * math.log(50) - 1.369)
        result = self.p.percent(F, 50, 158, parameter=PEREIRA_2007.Parameters.FEF50, value=pred)
        self.assertAlmostEqual(result, 100.0, places=2)
        self.assertGreater(pred, 2.5)
        self.assertLess(pred, 4.5)

    def test_printed_coefficient_would_be_wrong_by_a_factor_of_four(self):
        as_printed = math.exp(0.839 * math.log(158) - 0.044 * math.log(50) - 1.369)
        self.assertGreater(as_printed, 14.0)  # vs a reported mean of 3.40 L/s
        pct = self.p.percent(F, 50, 158, parameter=PEREIRA_2007.Parameters.FEF50, value=3.40)
        self.assertGreater(pct, 90.0)  # would be ~23% with the printed coefficient

    def test_agrees_with_the_papers_own_fef50_fvc_ratio_equation(self):
        # FEF50/FVC and FVC are both intact in Table 4; their product must be
        # consistent with the (repaired) FEF50 equation.
        fvc = 0.0441 * 158 - 0.0189 * 50 - 2.848
        ratio_pct = math.exp(-1.56 * math.log(158) - 0.175 * math.log(50) + 13.21)
        implied = ratio_pct / 100.0 * fvc
        pct = self.p.percent(F, 50, 158, parameter=PEREIRA_2007.Parameters.FEF50, value=implied)
        self.assertAlmostEqual(pct, 100.0, delta=10.0)


class TestPereira2007Weight(unittest.TestCase):

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_male_weight_param_without_weight_returns_na(self):
        for name in ('FVC_WT', 'FEV6_WT', 'FEV1_WT'):
            self.assertTrue(pd.isna(
                self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters[name], value=4.6)),
                msg=name)

    def test_female_weight_param_returns_na_even_with_weight(self):
        for name in ('FVC_WT', 'FEV6_WT', 'FEV1_WT'):
            self.assertTrue(pd.isna(
                self.p.percent(F, 50, 158, parameter=PEREIRA_2007.Parameters[name],
                               value=3.1, weight=65)),
                msg=name)

    def test_female_weight_param_lln_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.lln(F, 50, 158, parameter=PEREIRA_2007.Parameters.FVC_WT, weight=65)))

    def test_non_weight_params_ignore_weight(self):
        without = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)
        with_wt = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC,
                                 value=4.6, weight=95)
        self.assertEqual(without, with_wt)

    def test_weight_model_differs_from_height_age_model(self):
        plain = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)
        weighted = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC_WT,
                                  value=4.6, weight=95)
        self.assertNotEqual(plain, weighted)

    def test_heavier_men_have_lower_predicted_fvc(self):
        # The weight coefficient is negative (-0.0106), so %predicted rises with weight.
        light = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC_WT,
                               value=4.6, weight=60)
        heavy = self.p.percent(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC_WT,
                               value=4.6, weight=100)
        self.assertGreater(heavy, light)


class TestPereira2007LLN(unittest.TestCase):

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_male_linear_lln_offsets(self):
        for name, pred, offset in (
                ('FVC', 0.0517 * 171 - 0.0207 * 48 - 3.18, 0.90),
                ('FEV6', 0.0521 * 171 - 0.0229 * 48 - 3.179, 0.87),
                ('FEV1', 0.0338 * 171 - 0.0252 * 48 - 0.789, 0.76),
                ('FEV1FVC', -0.175 * 171 - 0.197 * 48 + 120.3, 7.6),
                ('FEV1FEV6', -0.165 * 171 - 0.151 * 48 + 117.1, 6.9)):
            lln = self.p.lln(M, 48, 171, parameter=PEREIRA_2007.Parameters[name])
            self.assertAlmostEqual(lln, pred - offset, places=6, msg=name)

    def test_male_weight_model_lln_offsets(self):
        for name, pred, offset in (
                ('FVC_WT', 0.0599 * 171 - 0.0213 * 48 - 0.0106 * 78 - 3.748, 0.91),
                ('FEV6_WT', 0.0593 * 171 - 0.0235 * 48 - 0.00964 * 78 - 3.655, 0.89),
                ('FEV1_WT', 0.0398 * 171 - 0.0257 * 48 - 0.0077 * 78 - 1.201, 0.76)):
            lln = self.p.lln(M, 48, 171, parameter=PEREIRA_2007.Parameters[name], weight=78)
            self.assertAlmostEqual(lln, pred - offset, places=6, msg=name)

    def test_female_linear_lln_offsets(self):
        for name, pred, offset in (
                ('FVC', 0.0441 * 158 - 0.0189 * 50 - 2.848, 0.64),
                ('FEV1', 0.0314 * 158 - 0.0203 * 50 - 1.353, 0.61),
                ('FEV1FVC', -0.140 * 158 - 0.158 * 50 + 111.5, 8.50),
                ('FEV1FEV6', -0.107 * 158 - 0.141 * 50 + 105.9, 7.90)):
            lln = self.p.lln(F, 50, 158, parameter=PEREIRA_2007.Parameters[name])
            self.assertAlmostEqual(lln, pred - offset, places=6, msg=name)

    def test_female_fev6_uses_lower_limit_column_not_residual_column(self):
        # Table 4 prints residual 0.53 but lower limit "P - 0.63"; the latter wins.
        pred = 0.0437 * 158 - 0.0196 * 50 - 2.769
        lln = self.p.lln(F, 50, 158, parameter=PEREIRA_2007.Parameters.FEV6)
        self.assertAlmostEqual(lln, pred - 0.63, places=6)

    def test_male_log_lln_factors(self):
        for name, c_ht, c_age, const, factor in (
                ('PEF', 0.830, -0.114, -1.43, 0.76),
                ('FEF50', 0.0, -0.529, 3.55, 0.60),
                ('FEF75', 0.0, -1.071, 4.46, 0.60),
                ('FEF25_75', 0.0, -0.687, 3.93, 0.59),
                ('FEF75_85', 0.0, -1.169, 4.39, 0.58)):
            pred = math.exp(c_ht * math.log(171) + c_age * math.log(48) + const)
            lln = self.p.lln(M, 48, 171, parameter=PEREIRA_2007.Parameters[name])
            self.assertAlmostEqual(lln, pred * factor, places=6, msg=name)

    def test_female_log_lln_factors(self):
        for name, c_ht, c_age, const, factor in (
                ('PEF', 1.442, -0.125, -4.863, 0.75),
                ('FEF50', 0.839, -0.444, -1.369, 0.56),
                ('FEF75', 1.097, -0.952, -1.922, 0.53),
                ('FEF25_75', 0.998, -0.588, -1.852, 0.57),
                ('FEF75_85', 1.382, -1.089, -3.279, 0.52)):
            pred = math.exp(c_ht * math.log(158) + c_age * math.log(50) + const)
            lln = self.p.lln(F, 50, 158, parameter=PEREIRA_2007.Parameters[name])
            self.assertAlmostEqual(lln, pred * factor, places=6, msg=name)

    def test_lln_is_below_predicted_for_every_parameter(self):
        for name in ALL_PARAMS:
            param = PEREIRA_2007.Parameters[name]
            lln = self.p.lln(M, 48, 171, parameter=param, weight=78)
            pct = self.p.percent(M, 48, 171, parameter=param, value=lln, weight=78)
            self.assertLess(pct, 100.0, msg=name)


class TestPereira2007ManuscriptClaims(unittest.TestCase):

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_male_fev1fvc_lln_reaches_70_percent_at_age_65(self):
        # Results: "The lower limit of 70% is, on average, reached at 65 years
        # of age for males and at 70 years of age for females."
        lln = self.p.lln(M, 65, MALE_HT, parameter=PEREIRA_2007.Parameters.FEV1FVC)
        self.assertAlmostEqual(lln, 70.0, delta=0.5)

    def test_female_fev1fvc_lln_reaches_70_percent_at_age_70(self):
        lln = self.p.lln(F, 70, FEMALE_HT, parameter=PEREIRA_2007.Parameters.FEV1FVC)
        self.assertAlmostEqual(lln, 70.0, delta=0.5)

    def test_female_fev1_declines_about_20_ml_per_year(self):
        # Results: "FEV1, on average, drops 26 mL/year in males and 20 mL/year in females."
        a = self.p.lln(F, 50, FEMALE_HT, parameter=PEREIRA_2007.Parameters.FEV1)
        b = self.p.lln(F, 51, FEMALE_HT, parameter=PEREIRA_2007.Parameters.FEV1)
        self.assertAlmostEqual((a - b) * 1000, 20.3, places=4)

    def test_male_fev1_declines_about_26_ml_per_year(self):
        # The weight model's age coefficient (-0.0257) is the one that rounds to 26 mL.
        a = self.p.lln(M, 48, MALE_HT, parameter=PEREIRA_2007.Parameters.FEV1_WT, weight=MALE_WT)
        b = self.p.lln(M, 49, MALE_HT, parameter=PEREIRA_2007.Parameters.FEV1_WT, weight=MALE_WT)
        self.assertAlmostEqual((a - b) * 1000, 25.7, places=4)

    def test_height_negatively_influences_ratios_in_both_sexes(self):
        # Results: "Height negatively influenced predicted values for the
        # FEV1/FVC, FEV1/FEV6 and flows/FVC ratios in both genders."
        cases = ((M, 48, 155, 190), (F, 50, 145, 180))
        ratios = ('FEV1FVC', 'FEV1FEV6', 'FEF50_FVC', 'FEF75_FVC',
                  'FEF25_75_FVC', 'FEF75_85_FVC')
        for sex, age, short, tall in cases:
            for name in ratios:
                param = PEREIRA_2007.Parameters[name]
                lln_short = self.p.lln(sex, age, short, parameter=param)
                lln_tall = self.p.lln(sex, age, tall, parameter=param)
                self.assertLess(lln_tall, lln_short, msg=f'{name} sex={sex}')


class TestPereira2007Unavailable(unittest.TestCase):
    """No SEE or residual SD was published."""

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_zscore_is_na(self):
        self.assertTrue(pd.isna(
            self.p.zscore(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)))

    def test_uln_is_na(self):
        self.assertTrue(pd.isna(self.p.uln(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC)))

    def test_lms_is_na_triple(self):
        l, m, s = self.p.lms(M, 48, 171, parameter=PEREIRA_2007.Parameters.FVC)
        self.assertTrue(pd.isna(l) and pd.isna(m) and pd.isna(s))


class TestPereira2007OutOfRange(unittest.TestCase):

    def setUp(self):
        self.p = PEREIRA_2007()

    def test_male_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(M, 25, 171, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)))

    def test_male_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(M, 87, 171, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)))

    def test_female_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(F, 19, 158, parameter=PEREIRA_2007.Parameters.FVC, value=3.1)))

    def test_female_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(F, 86, 158, parameter=PEREIRA_2007.Parameters.FVC, value=3.1)))

    def test_male_height_out_of_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(M, 48, 151, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)))
        self.assertTrue(pd.isna(
            self.p.percent(M, 48, 193, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)))

    def test_female_height_out_of_range_returns_na(self):
        self.assertTrue(pd.isna(
            self.p.percent(F, 50, 136, parameter=PEREIRA_2007.Parameters.FVC, value=3.1)))
        self.assertTrue(pd.isna(
            self.p.percent(F, 50, 183, parameter=PEREIRA_2007.Parameters.FVC, value=3.1)))

    def test_lln_out_of_range_returns_na(self):
        self.assertTrue(pd.isna(self.p.lln(M, 25, 171, parameter=PEREIRA_2007.Parameters.FVC)))

    def test_closest_strategy_clamps_age_to_boundary(self):
        self.p.set_strategy('closest')
        clamped = self.p.percent(M, 20, 171, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)
        at_bound = self.p.percent(M, 26, 171, parameter=PEREIRA_2007.Parameters.FVC, value=4.6)
        self.assertEqual(clamped, at_bound)


class TestPereira2007Compute(unittest.TestCase):

    def setUp(self):
        self.p = PEREIRA_2007()
        self.df = pd.DataFrame({
            'sex': [M, F],
            'age': [48.0, 50.0],
            'height': [171.0, 158.0],
            'weight': [78.0, 65.0],
            'FVC': [4.64, 3.14],
        })

    def test_compute_without_weight_col_raises(self):
        # percent()/lln() take a weight argument, so compute() demands the column.
        with self.assertRaises(ValueError):
            self.p.compute(self.df, PEREIRA_2007.Parameters.FVC, value_col='FVC')

    def test_compute_percent_matches_scalar_call(self):
        out = self.p.compute(self.df, PEREIRA_2007.Parameters.FVC,
                             value_col='FVC', weight_col='weight', metrics=('percent',))
        scalar = self.p.percent(M, 48.0, 171.0, parameter=PEREIRA_2007.Parameters.FVC,
                                value=4.64, weight=78.0)
        self.assertAlmostEqual(out['percent'].iloc[0], scalar, places=6)

    def test_compute_lln_matches_scalar_call(self):
        out = self.p.compute(self.df, PEREIRA_2007.Parameters.FVC,
                             weight_col='weight', metrics=('lln',))
        scalar = self.p.lln(F, 50.0, 158.0, parameter=PEREIRA_2007.Parameters.FVC, weight=65.0)
        self.assertAlmostEqual(out['lln'].iloc[1], scalar, places=6)

    def test_compute_weight_param_yields_na_for_the_female_row(self):
        out = self.p.compute(self.df, PEREIRA_2007.Parameters.FVC_WT,
                             value_col='FVC', weight_col='weight', metrics=('percent',))
        self.assertFalse(pd.isna(out['percent'].iloc[0]))
        self.assertTrue(pd.isna(out['percent'].iloc[1]))


if __name__ == '__main__':
    unittest.main()

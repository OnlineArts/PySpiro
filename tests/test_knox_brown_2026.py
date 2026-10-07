import unittest

import pandas as pd

from pyspiro import KNOX_BROWN_2026, GLI_2017, GLI_2021, GLI_2012, BOWERMAN_2022


P = KNOX_BROWN_2026.Parameters


class TestPercentile1(unittest.TestCase):
    """Consensus 1st percentile values, table 2 of Knox-Brown 2026."""

    def setUp(self):
        self.q = KNOX_BROWN_2026()

    # ── Sex-specific parameters ────────────────────────────────────────────

    def test_fev1_male(self):
        self.assertEqual(self.q.percentile1(P.FEV1, sex=1), 0.50)

    def test_fev1_female(self):
        self.assertEqual(self.q.percentile1(P.FEV1, sex=0), 0.40)

    def test_fvc_male(self):
        self.assertEqual(self.q.percentile1(P.FVC, sex=1), 1.50)

    def test_fvc_female(self):
        self.assertEqual(self.q.percentile1(P.FVC, sex=0), 1.20)

    def test_va_male(self):
        self.assertEqual(self.q.percentile1(P.VA, sex=1), 2.40)

    def test_va_female(self):
        self.assertEqual(self.q.percentile1(P.VA, sex=0), 2.00)

    def test_tlc_male(self):
        self.assertEqual(self.q.percentile1(P.TLC, sex=1), 2.60)

    def test_tlc_female(self):
        self.assertEqual(self.q.percentile1(P.TLC, sex=0), 2.30)

    # ── Sex-neutral parameters ─────────────────────────────────────────────

    def test_fev1fvc_is_sex_neutral(self):
        self.assertEqual(self.q.percentile1(P.FEV1FVC), 0.15)
        self.assertEqual(self.q.percentile1(P.FEV1FVC, sex=1), 0.15)
        self.assertEqual(self.q.percentile1(P.FEV1FVC, sex=0), 0.15)

    def test_dlco_si_is_sex_neutral(self):
        self.assertEqual(self.q.percentile1(P.DLCO_SI), 1.60)
        self.assertEqual(self.q.percentile1(P.DLCO_SI, sex=0), 1.60)

    def test_kco_si_is_sex_neutral(self):
        self.assertEqual(self.q.percentile1(P.KCO_SI), 0.40)
        self.assertEqual(self.q.percentile1(P.KCO_SI, sex=1), 0.40)

    # ── Derived traditional units ──────────────────────────────────────────

    def test_dlco_traditional_conversion(self):
        self.assertAlmostEqual(self.q.percentile1(P.DLCO_trad), 1.60 * 2.9863, places=6)

    def test_kco_traditional_conversion(self):
        self.assertAlmostEqual(self.q.percentile1(P.KCO_trad), 0.40 * 2.9863, places=6)

    # ── Sex classification helper ──────────────────────────────────────────

    def test_is_sex_specific(self):
        for parameter in (P.FEV1, P.FVC, P.VA, P.TLC):
            self.assertTrue(self.q.is_sex_specific(parameter))
        for parameter in (P.FEV1FVC, P.DLCO_SI, P.DLCO_trad, P.KCO_SI, P.KCO_trad):
            self.assertFalse(self.q.is_sex_specific(parameter))

    # ── Invalid input ──────────────────────────────────────────────────────

    def test_missing_sex_for_sex_specific_parameter(self):
        self.assertTrue(pd.isna(self.q.percentile1(P.FEV1)))

    def test_invalid_sex_code(self):
        self.assertTrue(pd.isna(self.q.percentile1(P.FEV1, sex=2)))

    def test_unknown_parameter(self):
        self.assertTrue(pd.isna(self.q.percentile1(99, sex=1)))

    def test_integer_parameter_accepted(self):
        self.assertEqual(self.q.percentile1(P.FEV1.value, sex=1), 0.50)


class TestQuotient(unittest.TestCase):

    def setUp(self):
        self.q = KNOX_BROWN_2026()

    def test_fev1q_female(self):
        # 1.20 L / 0.40 L
        self.assertEqual(self.q.quotient(P.FEV1, 1.20, sex=0), 3.00)

    def test_fev1q_male(self):
        # 1.20 L / 0.50 L
        self.assertEqual(self.q.quotient(P.FEV1, 1.20, sex=1), 2.40)

    def test_same_value_differs_by_sex(self):
        self.assertNotEqual(self.q.quotient(P.FVC, 3.00, sex=0),
                            self.q.quotient(P.FVC, 3.00, sex=1))

    def test_fvcq_male(self):
        self.assertEqual(self.q.quotient(P.FVC, 3.00, sex=1), 2.00)

    def test_dlcoq(self):
        self.assertEqual(self.q.quotient(P.DLCO_SI, 4.80), 3.00)

    def test_kcoq(self):
        self.assertEqual(self.q.quotient(P.KCO_SI, 1.20), 3.00)

    def test_vaq_female(self):
        self.assertEqual(self.q.quotient(P.VA, 4.00, sex=0), 2.00)

    def test_tlcq_male(self):
        self.assertEqual(self.q.quotient(P.TLC, 5.20, sex=1), 2.00)

    def test_quotient_at_first_percentile_is_one(self):
        self.assertEqual(self.q.quotient(P.FEV1, 0.50, sex=1), 1.00)

    def test_quotient_below_first_percentile(self):
        self.assertEqual(self.q.quotient(P.FEV1, 0.25, sex=1), 0.50)

    def test_traditional_and_si_agree_for_equivalent_values(self):
        si = self.q.quotient(P.DLCO_SI, 4.80)
        trad = self.q.quotient(P.DLCO_trad, 4.80 * 2.9863)
        self.assertAlmostEqual(si, trad, places=2)

    # ── Ratio notation ─────────────────────────────────────────────────────

    def test_fev1fvc_as_fraction(self):
        self.assertEqual(self.q.quotient(P.FEV1FVC, 0.60), 4.00)

    def test_fev1fvc_percentage_notation_rejected(self):
        # A quotient can legitimately exceed 1, so 0-100 input cannot be
        # auto-detected the way the severity classifiers do it.
        self.assertTrue(pd.isna(self.q.quotient(P.FEV1FVC, 60)))

    def test_fev1fvc_at_one_is_accepted(self):
        self.assertFalse(pd.isna(self.q.quotient(P.FEV1FVC, 1.0)))

    # ── Invalid input ──────────────────────────────────────────────────────

    def test_missing_sex(self):
        self.assertTrue(pd.isna(self.q.quotient(P.FEV1, 1.20)))

    def test_none_value(self):
        self.assertTrue(pd.isna(self.q.quotient(P.FEV1, None, sex=1)))

    def test_na_value(self):
        self.assertTrue(pd.isna(self.q.quotient(P.FEV1, pd.NA, sex=1)))

    def test_negative_value(self):
        self.assertTrue(pd.isna(self.q.quotient(P.FEV1, -1.0, sex=1)))

    def test_non_numeric_value(self):
        self.assertTrue(pd.isna(self.q.quotient(P.FEV1, "abc", sex=1)))


class TestBand(unittest.TestCase):

    def setUp(self):
        self.q = KNOX_BROWN_2026()

    def test_band_is_floor_of_quotient(self):
        # 1.20 / 0.40 = 3.00
        self.assertEqual(self.q.band(P.FEV1, 1.20, sex=0), 3)
        # 1.15 / 0.40 = 2.88
        self.assertEqual(self.q.band(P.FEV1, 1.15, sex=0), 2)

    def test_band_zero_at_first_percentile_boundary(self):
        self.assertEqual(self.q.band(P.FEV1, 0.30, sex=1), 0)

    def test_band_one_at_exactly_the_first_percentile(self):
        self.assertEqual(self.q.band(P.FEV1, 0.50, sex=1), 1)

    def test_band_capped_at_max(self):
        self.assertEqual(self.q.band(P.FEV1, 9.90, sex=1), KNOX_BROWN_2026.MAX_BAND)
        self.assertEqual(KNOX_BROWN_2026.MAX_BAND, 6)

    def test_band_na_on_invalid_input(self):
        self.assertTrue(pd.isna(self.q.band(P.FEV1, 1.20)))


class TestCompute(unittest.TestCase):

    def setUp(self):
        self.q = KNOX_BROWN_2026()
        self.df = pd.DataFrame({
            "sex":  [0, 1, 0],
            "FEV1": [1.20, 2.50, 0.30],
            "DLCO": [4.80, 1.60, 0.80],
        })

    def test_quotient_column(self):
        result = self.q.compute(self.df, P.FEV1, value_col="FEV1")
        self.assertEqual(list(result.columns), ["quotient"])
        self.assertEqual(result["quotient"].tolist(), [3.00, 5.00, 0.75])

    def test_all_metrics(self):
        result = self.q.compute(self.df, P.FEV1, value_col="FEV1",
                                metrics=("quotient", "percentile1", "band"))
        self.assertEqual(list(result.columns), ["quotient", "percentile1", "band"])
        self.assertEqual(result["percentile1"].tolist(), [0.40, 0.50, 0.40])
        self.assertEqual(result["band"].tolist(), [3, 5, 0])

    def test_index_preserved(self):
        df = self.df.copy()
        df.index = ["a", "b", "c"]
        result = self.q.compute(df, P.FEV1, value_col="FEV1")
        self.assertEqual(list(result.index), ["a", "b", "c"])

    def test_sex_neutral_parameter_without_sex_column(self):
        result = self.q.compute(self.df, P.DLCO_SI, value_col="DLCO", sex_col=None)
        self.assertEqual(result["quotient"].tolist(), [3.00, 1.00, 0.50])

    def test_custom_sex_column(self):
        df = self.df.rename(columns={"sex": "gender"})
        result = self.q.compute(df, P.FEV1, value_col="FEV1", sex_col="gender")
        self.assertEqual(result["quotient"].tolist(), [3.00, 5.00, 0.75])

    def test_sex_specific_parameter_requires_sex_column(self):
        with self.assertRaises(ValueError):
            self.q.compute(self.df, P.FEV1, value_col="FEV1", sex_col=None)

    def test_unknown_metric_raises(self):
        with self.assertRaises(ValueError):
            self.q.compute(self.df, P.FEV1, value_col="FEV1", metrics=("zscore",))

    def test_unknown_parameter_raises(self):
        with self.assertRaises(ValueError):
            self.q.compute(self.df, 99, value_col="FEV1")

    def test_missing_value_col_raises(self):
        with self.assertRaises(ValueError):
            self.q.compute(self.df, P.FEV1, value_col=None)

    def test_percentile1_only_needs_no_value_col(self):
        result = self.q.compute(self.df, P.FEV1, value_col=None, metrics=("percentile1",))
        self.assertEqual(result["percentile1"].tolist(), [0.40, 0.50, 0.40])


class TestHazardRatio(unittest.TestCase):
    """Table 4 (adjusted) and supplementary table S3 (unadjusted)."""

    def setUp(self):
        self.q = KNOX_BROWN_2026()

    def test_cuh_fev1_model1(self):
        hr = self.q.hazard_ratio(P.FEV1, site="CUH", model="model1")
        self.assertEqual(hr["hr"], 0.77)
        self.assertEqual(hr["ci"], (0.74, 0.80))

    def test_rph_va_model2_strongest_association(self):
        hr = self.q.hazard_ratio(P.VA, site="RPH", model="model2")
        self.assertEqual(hr["hr"], 0.31)

    def test_fev1fvc_not_significant_after_adjustment(self):
        for site, p_value in (("CUH", "0.545"), ("RPH", "0.705")):
            hr = self.q.hazard_ratio(P.FEV1FVC, site=site, model="model2")
            self.assertEqual(hr["p"], p_value)

    def test_unadjusted_includes_c_index(self):
        hr = self.q.hazard_ratio(P.DLCO_SI, site="RPH", model="unadjusted")
        self.assertEqual(hr["hr"], 0.51)
        self.assertEqual(hr["c_index"], 0.73)
        self.assertEqual(hr["c_index_ci"], (0.72, 0.73))

    def test_adjusted_models_have_no_c_index(self):
        self.assertNotIn("c_index", self.q.hazard_ratio(P.DLCO_SI, model="model1"))

    def test_traditional_units_alias_to_si(self):
        self.assertEqual(self.q.hazard_ratio(P.KCO_trad, site="CUH", model="model1"),
                         self.q.hazard_ratio(P.KCO_SI, site="CUH", model="model1"))
        self.assertEqual(self.q.hazard_ratio(P.DLCO_trad, site="RPH", model="unadjusted"),
                         self.q.hazard_ratio(P.DLCO_SI, site="RPH", model="unadjusted"))

    def test_returned_dict_is_a_copy(self):
        hr = self.q.hazard_ratio(P.FEV1, site="CUH", model="model1")
        hr["hr"] = 99
        self.assertEqual(self.q.hazard_ratio(P.FEV1, site="CUH", model="model1")["hr"], 0.77)

    def test_every_parameter_and_model_present_for_both_sites(self):
        for site in ("CUH", "RPH"):
            for parameter in (P.FEV1, P.FVC, P.FEV1FVC, P.DLCO_SI, P.KCO_SI, P.VA, P.TLC):
                for model in ("unadjusted", "model1", "model2"):
                    hr = self.q.hazard_ratio(parameter, site=site, model=model)
                    self.assertIn("hr", hr)
                    self.assertEqual(len(hr["ci"]), 2)

    def test_invalid_site(self):
        self.assertEqual(self.q.hazard_ratio(P.FEV1, site="XYZ"), {})

    def test_invalid_model(self):
        self.assertEqual(self.q.hazard_ratio(P.FEV1, model="model3"), {})

    def test_invalid_parameter(self):
        self.assertEqual(self.q.hazard_ratio(99), {})


class TestCohortReference(unittest.TestCase):
    """Supplementary tables S1 (CUH) and S2 (RPH)."""

    STRATA = ("overall", "male", "female", "age_lt_40", "age_40_49",
              "age_50_59", "age_60_69", "age_ge_70")

    def setUp(self):
        self.q = KNOX_BROWN_2026()

    def test_cuh_overall_fev1q(self):
        ref = self.q.cohort_reference(P.FEV1, site="CUH", stratum="overall")
        self.assertEqual(ref["n"], 7717)
        self.assertEqual(ref["mean"], 5.54)
        self.assertEqual(ref["sd"], 2.07)

    def test_rph_overall_n(self):
        self.assertEqual(self.q.cohort_reference(P.FEV1, site="RPH")["n"], 6054)

    def test_fev1fvc_reported_as_median_and_iqr(self):
        ref = self.q.cohort_reference(P.FEV1FVC, site="CUH", stratum="overall")
        self.assertEqual(ref["median"], 4.32)
        self.assertEqual(ref["iqr"], (1.86, 5.03))
        self.assertNotIn("mean", ref)

    def test_quotients_decline_with_age(self):
        ages = ("age_lt_40", "age_40_49", "age_50_59", "age_60_69", "age_ge_70")
        for site in ("CUH", "RPH"):
            means = [self.q.cohort_reference(P.FEV1, site=site, stratum=s)["mean"]
                     for s in ages]
            self.assertEqual(means, sorted(means, reverse=True))

    def test_suspect_standard_deviations_recorded_as_none(self):
        # Both source tables carry an SD that is out of keeping with its neighbours.
        self.assertIsNone(self.q.cohort_reference(P.TLC, site="CUH", stratum="female")["sd"])
        self.assertIsNone(self.q.cohort_reference(P.VA, site="RPH", stratum="overall")["sd"])

    def test_traditional_units_alias_to_si(self):
        self.assertEqual(self.q.cohort_reference(P.DLCO_trad, site="CUH"),
                         self.q.cohort_reference(P.DLCO_SI, site="CUH"))

    def test_all_strata_present_for_all_parameters(self):
        for site in ("CUH", "RPH"):
            for stratum in self.STRATA:
                for parameter in (P.FEV1, P.FVC, P.FEV1FVC, P.DLCO_SI,
                                  P.KCO_SI, P.VA, P.TLC):
                    ref = self.q.cohort_reference(parameter, site=site, stratum=stratum)
                    self.assertIn("n", ref)

    def test_sex_strata_sum_to_overall(self):
        for site in ("CUH", "RPH"):
            overall = self.q.cohort_reference(P.FEV1, site=site, stratum="overall")["n"]
            male = self.q.cohort_reference(P.FEV1, site=site, stratum="male")["n"]
            female = self.q.cohort_reference(P.FEV1, site=site, stratum="female")["n"]
            self.assertEqual(male + female, overall)

    def test_age_strata_sum_to_overall(self):
        ages = ("age_lt_40", "age_40_49", "age_50_59", "age_60_69", "age_ge_70")
        for site in ("CUH", "RPH"):
            overall = self.q.cohort_reference(P.FEV1, site=site, stratum="overall")["n"]
            total = sum(self.q.cohort_reference(P.FEV1, site=site, stratum=s)["n"]
                        for s in ages)
            self.assertEqual(total, overall)

    def test_invalid_stratum(self):
        self.assertEqual(self.q.cohort_reference(P.FEV1, stratum="age_100"), {})

    def test_invalid_site(self):
        self.assertEqual(self.q.cohort_reference(P.FEV1, site="XYZ"), {})


class TestNonWhitePercentiles(unittest.TestCase):
    """Table 2, non-White CUH patients — provided for sensitivity checks only."""

    def test_values_and_confidence_intervals(self):
        table = KNOX_BROWN_2026.NON_WHITE_PERCENTILE_1
        value, ci = table[P.FEV1.value]["male"]
        self.assertEqual(value, 0.52)
        self.assertEqual(ci, (0.43, 0.73))

    def test_consensus_values_lie_within_published_confidence_intervals(self):
        # The authors state the non-White 1st percentiles "were similar to those of
        # the consensus 1st percentile for all lung function measurements".  That
        # holds everywhere except female KCO, which is tested separately below.
        q = KNOX_BROWN_2026()
        for parameter, rows in KNOX_BROWN_2026.NON_WHITE_PERCENTILE_1.items():
            for label, sex in (("male", 1), ("female", 0)):
                if parameter == P.KCO_SI.value and label == "female":
                    continue
                _, (low, high) = rows[label]
                consensus = q.percentile1(parameter, sex=sex)
                self.assertTrue(low <= consensus <= high,
                                "%s %s: %.2f outside (%.2f, %.2f)"
                                % (KNOX_BROWN_2026.Parameters(parameter).name,
                                   label, consensus, low, high))

    def test_female_kco_consensus_falls_outside_the_non_white_interval(self):
        # Table 2: non-White females at CUH had a KCO 1st percentile of
        # 0.79 (0.59-1.00) against a consensus of 0.40 -- roughly double, with the
        # consensus value outside the confidence interval.  Documented, not asserted
        # away, because it qualifies the paper's claim of ethnic invariance.
        value, (low, high) = KNOX_BROWN_2026.NON_WHITE_PERCENTILE_1[P.KCO_SI.value]["female"]
        self.assertEqual((value, low, high), (0.79, 0.59, 1.00))
        self.assertLess(KNOX_BROWN_2026().percentile1(P.KCO_SI), low)


class TestExpressions(unittest.TestCase):

    def setUp(self):
        self.q = KNOX_BROWN_2026()

    def test_quotient_only_without_equation(self):
        out = self.q.expressions(P.FEV1, 2.50, sex=1)
        self.assertEqual(out["parameter"], "FEV1")
        self.assertEqual(out["percentile_1"], 0.50)
        self.assertEqual(out["quotient"], 5.00)
        self.assertEqual(out["band"], 5)
        self.assertNotIn("percent", out)

    def test_with_race_neutral_equation(self):
        out = self.q.expressions(P.FEV1, 2.50, sex=1, equation=BOWERMAN_2022(),
                                 equation_parameter=BOWERMAN_2022.Parameters.FEV1,
                                 age=64, height=178)
        self.assertEqual(out["equation"], "BOWERMAN_2022")
        self.assertEqual(out["quotient"], 5.00)
        self.assertFalse(pd.isna(out["percent"]))
        self.assertFalse(pd.isna(out["zscore"]))

    def test_with_gas_transfer_equation(self):
        out = self.q.expressions(P.DLCO_SI, 3.20, sex=1, equation=GLI_2017(),
                                 equation_parameter=GLI_2017.Parameters.TLCO,
                                 age=64, height=178)
        self.assertEqual(out["quotient"], 2.00)
        self.assertFalse(pd.isna(out["zscore"]))

    def test_quotient_defined_where_equation_is_out_of_range(self):
        # GLI_2021 static lung volumes stop at age 80.
        out = self.q.expressions(P.TLC, 5.10, sex=1, equation=GLI_2021(),
                                 equation_parameter=GLI_2021.Parameters.TLC,
                                 age=82, height=178)
        self.assertTrue(pd.isna(out["percent"]))
        self.assertTrue(pd.isna(out["zscore"]))
        self.assertEqual(out["quotient"], 1.96)

    def test_ethnicity_stratified_equation(self):
        out = self.q.expressions(P.FEV1, 2.50, sex=1, equation=GLI_2012(),
                                 equation_parameter=GLI_2012.Parameters.FEV1,
                                 age=64, height=178, ethnicity=1)
        self.assertFalse(pd.isna(out["percent"]))

    def test_ethnicity_required_for_stratified_equation(self):
        with self.assertRaises(ValueError):
            self.q.expressions(P.FEV1, 2.50, sex=1, equation=GLI_2012(),
                               equation_parameter=GLI_2012.Parameters.FEV1,
                               age=64, height=178)

    def test_equation_parameter_required(self):
        with self.assertRaises(ValueError):
            self.q.expressions(P.FEV1, 2.50, sex=1, equation=BOWERMAN_2022(),
                               age=64, height=178)

    def test_age_and_height_required(self):
        with self.assertRaises(ValueError):
            self.q.expressions(P.FEV1, 2.50, sex=1, equation=BOWERMAN_2022(),
                               equation_parameter=BOWERMAN_2022.Parameters.FEV1)

    def test_unknown_parameter(self):
        self.assertEqual(self.q.expressions(99, 2.50, sex=1), {})


if __name__ == "__main__":
    unittest.main()

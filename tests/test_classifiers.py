import unittest
import pandas as pd
from pyspiro import GOLD, STAR, ATS_ERS_2022, BDR_2022, LF_SEVERITY_2022, BODE, GAP, GOLD_ABE


class TestGOLD(unittest.TestCase):

    def setUp(self):
        self.gold = GOLD()

    # ── Stage classification ────────────────────────────────────────────────

    def test_stage_1_mild(self):
        self.assertEqual(self.gold.classify(FEV1p=85), 1)

    def test_stage_1_at_boundary(self):
        self.assertEqual(self.gold.classify(FEV1p=80), 1)

    def test_stage_2_moderate(self):
        self.assertEqual(self.gold.classify(FEV1p=65), 2)

    def test_stage_2_at_lower_boundary(self):
        self.assertEqual(self.gold.classify(FEV1p=50), 2)

    def test_stage_3_severe(self):
        self.assertEqual(self.gold.classify(FEV1p=40), 3)

    def test_stage_3_at_lower_boundary(self):
        self.assertEqual(self.gold.classify(FEV1p=30), 3)

    def test_stage_4_very_severe(self):
        self.assertEqual(self.gold.classify(FEV1p=25), 4)

    def test_stage_4_at_zero(self):
        self.assertEqual(self.gold.classify(FEV1p=0), 4)

    # ── Fraction notation (0-1) accepted ───────────────────────────────────

    def test_fraction_notation_stage_1(self):
        self.assertEqual(self.gold.classify(FEV1p=0.85), 1)

    def test_fraction_notation_stage_2(self):
        self.assertEqual(self.gold.classify(FEV1p=0.65), 2)

    def test_fraction_notation_stage_4(self):
        self.assertEqual(self.gold.classify(FEV1p=0.25), 4)

    # ── Error handling ──────────────────────────────────────────────────────

    def test_wrong_kwarg_returns_na(self):
        result = self.gold.classify(wrong_arg=60)
        self.assertTrue(pd.isna(result))

    def test_too_many_kwargs_returns_na(self):
        result = self.gold.classify(FEV1p=60, FVC=4.0)
        self.assertTrue(pd.isna(result))

    # ── Ordering ────────────────────────────────────────────────────────────

    def test_order_is_1_to_4(self):
        self.assertEqual(self.gold.get_order(), [1, 2, 3, 4])


class TestSTAR(unittest.TestCase):

    def setUp(self):
        self.star = STAR()

    # ── Stage classification (percentage input) ─────────────────────────────

    def test_stage_1_mild(self):
        self.assertEqual(self.star.classify(FEV1_FVC=65), 1)

    def test_stage_1_at_lower_boundary(self):
        self.assertEqual(self.star.classify(FEV1_FVC=60), 1)

    def test_stage_2_moderate(self):
        self.assertEqual(self.star.classify(FEV1_FVC=55), 2)

    def test_stage_3_severe(self):
        self.assertEqual(self.star.classify(FEV1_FVC=45), 3)

    def test_stage_4_very_severe(self):
        self.assertEqual(self.star.classify(FEV1_FVC=35), 4)

    def test_not_obstructive_returns_na(self):
        result = self.star.classify(FEV1_FVC=75)
        self.assertTrue(pd.isna(result))

    # ── Two-argument form (FEV1 / FVC) ─────────────────────────────────────

    def test_two_arg_form_stage_1(self):
        # 2.5/4.0 = 0.625 = 62.5% → stage 1
        result = self.star.classify(FEV1=2.5, FVC=4.0)
        self.assertEqual(result, 1)

    def test_two_arg_form_not_obstructive(self):
        # 3.0/4.0 = 0.75 = 75% → NA
        result = self.star.classify(FEV1=3.0, FVC=4.0)
        self.assertTrue(pd.isna(result))

    # ── Fraction notation ───────────────────────────────────────────────────

    def test_fraction_notation_stage_2(self):
        self.assertEqual(self.star.classify(FEV1_FVC=0.55), 2)

    # ── Ordering ────────────────────────────────────────────────────────────

    def test_order_is_1_to_4(self):
        self.assertEqual(self.star.get_order(), [1, 2, 3, 4])


class TestATSERS2022(unittest.TestCase):

    def setUp(self):
        self.clf = ATS_ERS_2022()

    # ── Normal ──────────────────────────────────────────────────────────────

    def test_normal_all_above_lln(self):
        result = self.clf.classify(FEV1_z=0.5, FVC_z=0.3, FEV1FVC_z=0.2)
        self.assertEqual(result, ATS_ERS_2022.NORMAL)

    def test_normal_at_exactly_lln(self):
        result = self.clf.classify(FEV1_z=-1.645, FVC_z=-1.645, FEV1FVC_z=-1.645)
        # FEV1FVC_z = -1.645 is NOT < -1.645, so not obstructive → normal
        self.assertEqual(result, ATS_ERS_2022.NORMAL)

    # ── Obstructive ─────────────────────────────────────────────────────────

    def test_obstructive_pure(self):
        result = self.clf.classify(FEV1_z=-2.5, FVC_z=0.1, FEV1FVC_z=-2.0)
        self.assertEqual(result, ATS_ERS_2022.OBSTRUCTIVE)

    def test_obstructive_with_normal_tlc_means_air_trapping(self):
        result = self.clf.classify(FEV1_z=-2.5, FVC_z=-1.8,
                                   FEV1FVC_z=-2.0, TLC_z=0.5)
        self.assertEqual(result, ATS_ERS_2022.OBSTRUCTIVE)

    # ── Obstructive with reduced FVC (no TLC) ──────────────────────────────

    def test_obstructive_reduced_fvc_no_tlc(self):
        result = self.clf.classify(FEV1_z=-2.5, FVC_z=-2.0, FEV1FVC_z=-2.0)
        self.assertEqual(result, ATS_ERS_2022.OBSTRUCTIVE_REDUCED_FVC)

    def test_obstructive_reduced_fvc_tlc_na_treated_as_missing(self):
        result = self.clf.classify(FEV1_z=-2.5, FVC_z=-2.0,
                                   FEV1FVC_z=-2.0, TLC_z=pd.NA)
        self.assertEqual(result, ATS_ERS_2022.OBSTRUCTIVE_REDUCED_FVC)

    # ── Mixed obstructive-restrictive ───────────────────────────────────────

    def test_mixed_tlc_confirmed(self):
        result = self.clf.classify(FEV1_z=-2.5, FVC_z=-2.0,
                                   FEV1FVC_z=-2.0, TLC_z=-2.5)
        self.assertEqual(result, ATS_ERS_2022.MIXED)

    # ── Possible restriction (no TLC) ───────────────────────────────────────

    def test_possible_restriction_no_tlc(self):
        result = self.clf.classify(FEV1_z=-1.8, FVC_z=-2.0, FEV1FVC_z=0.3)
        self.assertEqual(result, ATS_ERS_2022.POSSIBLE_RESTRICTION)

    # ── Restrictive ─────────────────────────────────────────────────────────

    def test_restrictive_tlc_confirmed(self):
        result = self.clf.classify(FEV1_z=-1.8, FVC_z=-2.0,
                                   FEV1FVC_z=0.3, TLC_z=-2.5)
        self.assertEqual(result, ATS_ERS_2022.RESTRICTIVE)

    # ── Non-specific (NSIP) ─────────────────────────────────────────────────

    def test_nsip_tlc_normal_despite_low_fvc(self):
        result = self.clf.classify(FEV1_z=-1.8, FVC_z=-2.0,
                                   FEV1FVC_z=0.3, TLC_z=0.5)
        self.assertEqual(result, ATS_ERS_2022.NSIP)

    def test_nsip_discordant_fev1_low_fvc_normal(self):
        # Unusual pattern: FEV1 < LLN with normal FVC and ratio
        result = self.clf.classify(FEV1_z=-2.0, FVC_z=0.5, FEV1FVC_z=0.3)
        self.assertEqual(result, ATS_ERS_2022.NSIP)

    # ── TLC_z value handling ────────────────────────────────────────────────

    def test_tlc_z_none_treated_as_missing(self):
        result = self.clf.classify(FEV1_z=-1.8, FVC_z=-2.0,
                                   FEV1FVC_z=0.3, TLC_z=None)
        self.assertEqual(result, ATS_ERS_2022.POSSIBLE_RESTRICTION)

    def test_tlc_z_nonnumeric_treated_as_missing(self):
        result = self.clf.classify(FEV1_z=-1.8, FVC_z=-2.0,
                                   FEV1FVC_z=0.3, TLC_z="unavailable")
        self.assertEqual(result, ATS_ERS_2022.POSSIBLE_RESTRICTION)

    # ── Error handling ──────────────────────────────────────────────────────

    def test_missing_fev1_z_returns_na(self):
        result = self.clf.classify(FVC_z=0.0, FEV1FVC_z=0.0)
        self.assertTrue(pd.isna(result))

    def test_missing_fvc_z_returns_na(self):
        result = self.clf.classify(FEV1_z=0.0, FEV1FVC_z=0.0)
        self.assertTrue(pd.isna(result))

    def test_missing_fev1fvc_z_returns_na(self):
        result = self.clf.classify(FEV1_z=0.0, FVC_z=0.0)
        self.assertTrue(pd.isna(result))

    def test_nonnumeric_required_input_returns_na(self):
        result = self.clf.classify(FEV1_z="bad", FVC_z=0.0, FEV1FVC_z=0.0)
        self.assertTrue(pd.isna(result))

    # ── Pattern constants and ordering ──────────────────────────────────────

    def test_pattern_constants_defined(self):
        self.assertEqual(ATS_ERS_2022.NORMAL, "Normal")
        self.assertEqual(ATS_ERS_2022.OBSTRUCTIVE, "Obstructive")
        self.assertEqual(ATS_ERS_2022.MIXED, "Mixed obstructive-restrictive")
        self.assertEqual(ATS_ERS_2022.RESTRICTIVE, "Restrictive")
        self.assertEqual(ATS_ERS_2022.NSIP, "Non-specific (NSIP)")

    def test_order_contains_all_patterns(self):
        order = self.clf.get_order()
        self.assertIn(ATS_ERS_2022.NORMAL, order)
        self.assertIn(ATS_ERS_2022.OBSTRUCTIVE, order)
        self.assertIn(ATS_ERS_2022.OBSTRUCTIVE_REDUCED_FVC, order)
        self.assertIn(ATS_ERS_2022.MIXED, order)
        self.assertIn(ATS_ERS_2022.POSSIBLE_RESTRICTION, order)
        self.assertIn(ATS_ERS_2022.RESTRICTIVE, order)
        self.assertIn(ATS_ERS_2022.NSIP, order)
        self.assertEqual(len(order), 7)


# ══════════════════════════════════════════════════════════════════════════════
# BDR_2022
# ══════════════════════════════════════════════════════════════════════════════

class TestBDR2022Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(BDR_2022())

    def test_constants_defined(self):
        self.assertEqual(BDR_2022.POSITIVE_FEV1, "Positive (FEV1)")
        self.assertEqual(BDR_2022.POSITIVE_FVC,  "Positive (FVC)")
        self.assertEqual(BDR_2022.POSITIVE_BOTH, "Positive (FEV1 and FVC)")
        self.assertEqual(BDR_2022.NEGATIVE,       "Negative")

    def test_order_defined(self):
        self.assertEqual(len(BDR_2022().get_order()), 4)


class TestBDR2022Classification(unittest.TestCase):

    def setUp(self):
        self.bdr = BDR_2022()

    # ── Positive FEV1 ────────────────────────────────────────────────────────

    def test_positive_fev1_above_threshold(self):
        # (2.35 - 2.0) / 3.0 * 100 = 11.67% > 10%
        result = self.bdr.classify(pre_fev1=2.0, post_fev1=2.35, predicted_fev1=3.0)
        self.assertEqual(result, BDR_2022.POSITIVE_FEV1)

    def test_positive_fev1_exactly_at_threshold_is_negative(self):
        # (2.30 - 2.0) / 3.0 * 100 = 10.0% → not > 10% → Negative
        result = self.bdr.classify(pre_fev1=2.0, post_fev1=2.30, predicted_fev1=3.0)
        self.assertEqual(result, BDR_2022.NEGATIVE)

    # ── Positive FVC ─────────────────────────────────────────────────────────

    def test_positive_fvc_only(self):
        # FEV1: (2.10-2.0)/3.0*100 = 3.3% negative; FVC: (3.5-3.0)/4.0*100 = 12.5% positive
        result = self.bdr.classify(
            pre_fev1=2.0, post_fev1=2.10, predicted_fev1=3.0,
            pre_fvc=3.0,  post_fvc=3.50,  predicted_fvc=4.0,
        )
        self.assertEqual(result, BDR_2022.POSITIVE_FVC)

    # ── Both positive ────────────────────────────────────────────────────────

    def test_positive_both_fev1_and_fvc(self):
        result = self.bdr.classify(
            pre_fev1=2.0, post_fev1=2.35, predicted_fev1=3.0,
            pre_fvc=3.0,  post_fvc=3.50,  predicted_fvc=4.0,
        )
        self.assertEqual(result, BDR_2022.POSITIVE_BOTH)

    # ── Negative ─────────────────────────────────────────────────────────────

    def test_negative_both_below_threshold(self):
        result = self.bdr.classify(
            pre_fev1=2.0, post_fev1=2.20, predicted_fev1=3.0,
            pre_fvc=3.0,  post_fvc=3.25,  predicted_fvc=4.0,
        )
        self.assertEqual(result, BDR_2022.NEGATIVE)

    def test_negative_fev1_only(self):
        result = self.bdr.classify(pre_fev1=2.0, post_fev1=2.20, predicted_fev1=3.0)
        self.assertEqual(result, BDR_2022.NEGATIVE)

    # ── FVC-only input ────────────────────────────────────────────────────────

    def test_fvc_only_positive(self):
        result = self.bdr.classify(pre_fvc=3.0, post_fvc=3.5, predicted_fvc=4.0)
        self.assertEqual(result, BDR_2022.POSITIVE_FVC)

    def test_fvc_only_negative(self):
        result = self.bdr.classify(pre_fvc=3.0, post_fvc=3.2, predicted_fvc=4.0)
        self.assertEqual(result, BDR_2022.NEGATIVE)

    # ── Missing / incomplete inputs ───────────────────────────────────────────

    def test_no_inputs_returns_na(self):
        self.assertTrue(pd.isna(self.bdr.classify()))

    def test_partial_fev1_set_ignored_returns_na(self):
        # pre and post provided but predicted missing → no complete set
        self.assertTrue(pd.isna(self.bdr.classify(pre_fev1=2.0, post_fev1=2.4)))

    def test_partial_fvc_set_ignored_fev1_complete_negative(self):
        # FVC incomplete; FEV1 complete but below threshold → Negative
        result = self.bdr.classify(
            pre_fev1=2.0, post_fev1=2.20, predicted_fev1=3.0,
            pre_fvc=3.0,  post_fvc=3.40,  # no predicted_fvc
        )
        self.assertEqual(result, BDR_2022.NEGATIVE)

    def test_zero_predicted_returns_na(self):
        self.assertTrue(pd.isna(
            self.bdr.classify(pre_fev1=2.0, post_fev1=2.5, predicted_fev1=0.0)))


# ══════════════════════════════════════════════════════════════════════════════
# LF_SEVERITY_2022
# ══════════════════════════════════════════════════════════════════════════════

class TestSEVERITY2022Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(LF_SEVERITY_2022())

    def test_constants_defined(self):
        self.assertEqual(LF_SEVERITY_2022.NORMAL,    "Normal")
        self.assertEqual(LF_SEVERITY_2022.MILD,      "Mild")
        self.assertEqual(LF_SEVERITY_2022.MODERATE,  "Moderate")
        self.assertEqual(LF_SEVERITY_2022.SEVERE,    "Severe")
        self.assertEqual(LF_SEVERITY_2022.ABOVE_ULN, "Above ULN")


class TestSEVERITY2022Classification(unittest.TestCase):

    def setUp(self):
        self.sev = LF_SEVERITY_2022()

    # ── Normal ───────────────────────────────────────────────────────────────

    def test_normal_well_above_lln(self):
        self.assertEqual(self.sev.classify(z=0.0), LF_SEVERITY_2022.NORMAL)

    def test_normal_exactly_at_lln(self):
        # z = -1.645 → >= LLN → Normal
        self.assertEqual(self.sev.classify(z=-1.645), LF_SEVERITY_2022.NORMAL)

    # ── Mild ─────────────────────────────────────────────────────────────────

    def test_mild_mid_range(self):
        self.assertEqual(self.sev.classify(z=-2.0), LF_SEVERITY_2022.MILD)

    def test_mild_just_below_lln(self):
        self.assertEqual(self.sev.classify(z=-1.646), LF_SEVERITY_2022.MILD)

    def test_mild_at_lower_boundary(self):
        # z = -2.5 is the mild/moderate boundary; ≥ -2.5 → Mild
        self.assertEqual(self.sev.classify(z=-2.5), LF_SEVERITY_2022.MILD)

    # ── Moderate ─────────────────────────────────────────────────────────────

    def test_moderate_mid_range(self):
        self.assertEqual(self.sev.classify(z=-3.0), LF_SEVERITY_2022.MODERATE)

    def test_moderate_just_below_mild(self):
        self.assertEqual(self.sev.classify(z=-2.51), LF_SEVERITY_2022.MODERATE)

    def test_moderate_at_lower_boundary(self):
        # z = -4.0 is the moderate/severe boundary; ≥ -4.0 → Moderate
        self.assertEqual(self.sev.classify(z=-4.0), LF_SEVERITY_2022.MODERATE)

    # ── Severe ───────────────────────────────────────────────────────────────

    def test_severe_just_below_moderate(self):
        self.assertEqual(self.sev.classify(z=-4.01), LF_SEVERITY_2022.SEVERE)

    def test_severe_very_low(self):
        self.assertEqual(self.sev.classify(z=-6.8), LF_SEVERITY_2022.SEVERE)

    # ── Above ULN flag ───────────────────────────────────────────────────────

    def test_above_uln_flag_false_returns_normal(self):
        self.assertEqual(self.sev.classify(z=2.0, flag_uln=False), LF_SEVERITY_2022.NORMAL)

    def test_above_uln_flag_true_returns_above_uln(self):
        self.assertEqual(self.sev.classify(z=2.0, flag_uln=True), LF_SEVERITY_2022.ABOVE_ULN)

    def test_above_uln_exactly_at_uln_not_flagged(self):
        # z = +1.645 is not > ULN, so no flag even with flag_uln=True
        self.assertEqual(self.sev.classify(z=1.645, flag_uln=True), LF_SEVERITY_2022.NORMAL)

    # ── Invalid inputs ────────────────────────────────────────────────────────

    def test_missing_z_returns_na(self):
        self.assertTrue(pd.isna(self.sev.classify()))

    def test_nonnumeric_z_returns_na(self):
        self.assertTrue(pd.isna(self.sev.classify(z="bad")))

    def test_none_z_returns_na(self):
        self.assertTrue(pd.isna(self.sev.classify(z=None)))


# ══════════════════════════════════════════════════════════════════════════════
# BODE
# ══════════════════════════════════════════════════════════════════════════════

class TestBODEInstantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(BODE())

    def test_order_is_quartiles(self):
        self.assertEqual(BODE().get_order(), [1, 2, 3, 4])


class TestBODEScore(unittest.TestCase):

    def setUp(self):
        self.bode = BODE()

    # ── Minimum and maximum scores ────────────────────────────────────────────

    def test_score_zero_minimum(self):
        # B=0 (BMI>21), O=0 (FEV1≥65%), D=0 (mMRC≤1), E=0 (≥350 m) → 0
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=1, walk6m=400), 0)

    def test_score_ten_maximum(self):
        # B=1 (BMI≤21), O=3 (FEV1≤35%), D=3 (mMRC=4), E=3 (≤149 m) → 10
        self.assertEqual(self.bode.score(bmi=20, fev1p=30, mmrc=4, walk6m=100), 10)

    # ── BMI component ─────────────────────────────────────────────────────────

    def test_bmi_exactly_21_scores_1(self):
        self.assertEqual(self.bode.score(bmi=21, fev1p=70, mmrc=0, walk6m=400), 1)

    def test_bmi_above_21_scores_0(self):
        self.assertEqual(self.bode.score(bmi=21.1, fev1p=70, mmrc=0, walk6m=400), 0)

    # ── FEV1 component ────────────────────────────────────────────────────────

    def test_fev1_at_65_scores_0(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=65, mmrc=0, walk6m=400), 0)

    def test_fev1_at_64_scores_1(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=64, mmrc=0, walk6m=400), 1)

    def test_fev1_at_50_scores_1(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=50, mmrc=0, walk6m=400), 1)

    def test_fev1_at_49_scores_2(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=49, mmrc=0, walk6m=400), 2)

    def test_fev1_at_36_scores_2(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=36, mmrc=0, walk6m=400), 2)

    def test_fev1_at_35_scores_3(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=35, mmrc=0, walk6m=400), 3)

    def test_fev1_fraction_notation(self):
        # 0.65 treated as 65%
        self.assertEqual(self.bode.score(bmi=25, fev1p=0.65, mmrc=0, walk6m=400), 0)

    # ── mMRC component ────────────────────────────────────────────────────────

    def test_mmrc_0_scores_0(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=0, walk6m=400), 0)

    def test_mmrc_1_scores_0(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=1, walk6m=400), 0)

    def test_mmrc_2_scores_1(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=2, walk6m=400), 1)

    def test_mmrc_3_scores_2(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=3, walk6m=400), 2)

    def test_mmrc_4_scores_3(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=4, walk6m=400), 3)

    # ── 6MWT component ───────────────────────────────────────────────────────

    def test_walk_at_350_scores_0(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=0, walk6m=350), 0)

    def test_walk_at_349_scores_1(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=0, walk6m=349), 1)

    def test_walk_at_250_scores_1(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=0, walk6m=250), 1)

    def test_walk_at_249_scores_2(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=0, walk6m=249), 2)

    def test_walk_at_150_scores_2(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=0, walk6m=150), 2)

    def test_walk_at_149_scores_3(self):
        self.assertEqual(self.bode.score(bmi=25, fev1p=70, mmrc=0, walk6m=149), 3)

    # ── Missing inputs ────────────────────────────────────────────────────────

    def test_missing_bmi_returns_na(self):
        self.assertTrue(pd.isna(self.bode.score(fev1p=60, mmrc=2, walk6m=300)))

    def test_missing_fev1p_returns_na(self):
        self.assertTrue(pd.isna(self.bode.score(bmi=25, mmrc=2, walk6m=300)))

    def test_missing_mmrc_returns_na(self):
        self.assertTrue(pd.isna(self.bode.score(bmi=25, fev1p=60, walk6m=300)))

    def test_missing_walk_returns_na(self):
        self.assertTrue(pd.isna(self.bode.score(bmi=25, fev1p=60, mmrc=2)))


class TestBODEClassify(unittest.TestCase):

    def setUp(self):
        self.bode = BODE()

    def test_quartile_1_score_0(self):
        # B=0, O=0, D=0, E=0 → 0 → Q1
        self.assertEqual(self.bode.classify(bmi=25, fev1p=70, mmrc=0, walk6m=400), 1)

    def test_quartile_1_score_2(self):
        # B=1 (bmi≤21), O=1 (55%), D=0, E=0 → score 2 → Q1 (0–2)
        self.assertEqual(self.bode.classify(bmi=21, fev1p=55, mmrc=0, walk6m=400), 1)

    def test_quartile_2_score_3(self):
        # B=0, O=1, D=1, E=1 → 3 → Q2
        self.assertEqual(self.bode.classify(bmi=25, fev1p=55, mmrc=2, walk6m=300), 2)

    def test_quartile_2_score_4(self):
        # B=1, O=1, D=1, E=1 → 4 → Q2
        self.assertEqual(self.bode.classify(bmi=21, fev1p=55, mmrc=2, walk6m=300), 2)

    def test_quartile_3_score_5(self):
        # B=0, O=2, D=2, E=1 → 5 → Q3
        self.assertEqual(self.bode.classify(bmi=25, fev1p=40, mmrc=3, walk6m=300), 3)

    def test_quartile_3_score_6(self):
        # B=1, O=2, D=2, E=1 → 6 → Q3
        self.assertEqual(self.bode.classify(bmi=21, fev1p=40, mmrc=3, walk6m=300), 3)

    def test_quartile_4_score_7(self):
        # B=0, O=3, D=3, E=1 → 7 → Q4
        self.assertEqual(self.bode.classify(bmi=25, fev1p=30, mmrc=4, walk6m=300), 4)

    def test_quartile_4_score_10(self):
        self.assertEqual(self.bode.classify(bmi=20, fev1p=30, mmrc=4, walk6m=100), 4)

    def test_missing_input_returns_na(self):
        self.assertTrue(pd.isna(self.bode.classify(bmi=25, fev1p=60, mmrc=2)))


# ══════════════════════════════════════════════════════════════════════════════
# GAP
# ══════════════════════════════════════════════════════════════════════════════

class TestGAPInstantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(GAP())

    def test_order_is_stages(self):
        self.assertEqual(GAP().get_order(), ["I", "II", "III"])

    def test_mortality_dict_accessible(self):
        m = GAP.MORTALITY
        self.assertIn("I", m)
        self.assertIn("II", m)
        self.assertIn("III", m)
        self.assertAlmostEqual(m["I"]["1y"],   0.056)
        self.assertAlmostEqual(m["III"]["3y"], 0.768)


class TestGAPScore(unittest.TestCase):

    def setUp(self):
        self.gap = GAP()

    # ── Known values (paper Figure 2) ─────────────────────────────────────────

    def test_minimum_score_female_young_good_function(self):
        # G=0, A=0 (age≤60), FVC=0 (>75%), DLCO=0 (>55%) → 0
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=80, dlco_pct=60), 0)

    def test_score_4_male_63_moderate_function(self):
        # G=1, A=1 (63y), FVC=1 (60%), DLCO=1 (45%) → 4
        self.assertEqual(self.gap.score(sex=1, age=63, fvc_pct=60, dlco_pct=45), 4)

    def test_score_7_male_70_poor_function(self):
        # G=1, A=2 (70y), FVC=2 (<50%), DLCO=2 (≤35%) → 7
        self.assertEqual(self.gap.score(sex=1, age=70, fvc_pct=45, dlco_pct=30), 7)

    def test_maximum_score_cannot_perform_dlco(self):
        # G=1, A=2, FVC=2, DLCO_na=3 → 8
        self.assertEqual(self.gap.score(sex=1, age=70, fvc_pct=45, dlco_na=True), 8)

    # ── G component ──────────────────────────────────────────────────────────

    def test_male_adds_one_point_vs_female(self):
        base = self.gap.score(sex=0, age=55, fvc_pct=80, dlco_pct=60)
        male = self.gap.score(sex=1, age=55, fvc_pct=80, dlco_pct=60)
        self.assertEqual(male - base, 1)

    # ── A component ──────────────────────────────────────────────────────────

    def test_age_60_scores_0(self):
        self.assertEqual(self.gap.score(sex=0, age=60, fvc_pct=80, dlco_pct=60), 0)

    def test_age_61_scores_1(self):
        self.assertEqual(self.gap.score(sex=0, age=61, fvc_pct=80, dlco_pct=60), 1)

    def test_age_65_scores_1(self):
        self.assertEqual(self.gap.score(sex=0, age=65, fvc_pct=80, dlco_pct=60), 1)

    def test_age_66_scores_2(self):
        self.assertEqual(self.gap.score(sex=0, age=66, fvc_pct=80, dlco_pct=60), 2)

    # ── P (FVC) component ────────────────────────────────────────────────────

    def test_fvc_above_75_scores_0(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=76, dlco_pct=60), 0)

    def test_fvc_exactly_75_scores_1(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=75, dlco_pct=60), 1)

    def test_fvc_exactly_50_scores_1(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=50, dlco_pct=60), 1)

    def test_fvc_below_50_scores_2(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=49, dlco_pct=60), 2)

    # ── P (DLCO) component ───────────────────────────────────────────────────

    def test_dlco_above_55_scores_0(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=80, dlco_pct=56), 0)

    def test_dlco_exactly_55_scores_1(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=80, dlco_pct=55), 1)

    def test_dlco_exactly_36_scores_1(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=80, dlco_pct=36), 1)

    def test_dlco_exactly_35_scores_2(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=80, dlco_pct=35), 2)

    def test_dlco_na_flag_scores_3(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=80, dlco_na=True), 3)

    def test_dlco_none_scores_3(self):
        self.assertEqual(self.gap.score(sex=0, age=55, fvc_pct=80, dlco_pct=None), 3)

    # ── Missing required inputs ───────────────────────────────────────────────

    def test_missing_sex_returns_na(self):
        self.assertTrue(pd.isna(self.gap.score(age=60, fvc_pct=70, dlco_pct=50)))

    def test_missing_age_returns_na(self):
        self.assertTrue(pd.isna(self.gap.score(sex=1, fvc_pct=70, dlco_pct=50)))

    def test_missing_fvc_returns_na(self):
        self.assertTrue(pd.isna(self.gap.score(sex=1, age=60, dlco_pct=50)))


class TestGAPClassify(unittest.TestCase):

    def setUp(self):
        self.gap = GAP()

    def test_stage_i_score_0(self):
        self.assertEqual(self.gap.classify(sex=0, age=55, fvc_pct=80, dlco_pct=60), "I")

    def test_stage_i_score_3(self):
        # G=1, A=0, FVC=1, DLCO=1 → 3 → Stage I
        self.assertEqual(self.gap.classify(sex=1, age=55, fvc_pct=60, dlco_pct=45), "I")

    def test_stage_ii_score_4(self):
        self.assertEqual(self.gap.classify(sex=1, age=63, fvc_pct=60, dlco_pct=45), "II")

    def test_stage_ii_score_5(self):
        # G=1, A=1, FVC=1, DLCO=2 → 5 → Stage II
        self.assertEqual(self.gap.classify(sex=1, age=63, fvc_pct=60, dlco_pct=30), "II")

    def test_stage_iii_score_6(self):
        # G=0, A=2, FVC=2, DLCO=2 → 6 → Stage III
        self.assertEqual(self.gap.classify(sex=0, age=70, fvc_pct=45, dlco_pct=30), "III")

    def test_stage_iii_score_8(self):
        self.assertEqual(self.gap.classify(sex=1, age=70, fvc_pct=45, dlco_na=True), "III")

    def test_missing_input_returns_na(self):
        self.assertTrue(pd.isna(self.gap.classify(age=60, fvc_pct=70, dlco_pct=50)))


# ══════════════════════════════════════════════════════════════════════════════
# GOLD_ABE
# ══════════════════════════════════════════════════════════════════════════════

class TestGOLDABEInstantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(GOLD_ABE())

    def test_order_is_a_b_e(self):
        self.assertEqual(GOLD_ABE().get_order(), ["A", "B", "E"])


class TestGOLDABEClassification(unittest.TestCase):

    def setUp(self):
        self.abe = GOLD_ABE()

    # ── Group A ───────────────────────────────────────────────────────────────

    def test_group_a_no_exac_low_cat(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=0, cat=8), "A")

    def test_group_a_no_exac_low_mmrc(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=0, mmrc=1), "A")

    def test_group_a_one_exac_no_hosp_low_cat(self):
        # 1 moderate exacerbation is below the E threshold
        self.assertEqual(self.abe.classify(exac_moderate=1, exac_hospitalised=0, cat=5), "A")

    def test_group_a_cat_boundary_9(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=0, cat=9), "A")

    def test_group_a_mmrc_boundary_1(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=0, mmrc=1), "A")

    # ── Group B ───────────────────────────────────────────────────────────────

    def test_group_b_high_cat(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=0, cat=15), "B")

    def test_group_b_cat_boundary_10(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=0, cat=10), "B")

    def test_group_b_high_mmrc(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=0, mmrc=3), "B")

    def test_group_b_mmrc_boundary_2(self):
        self.assertEqual(self.abe.classify(exac_moderate=1, exac_hospitalised=0, mmrc=2), "B")

    def test_group_b_high_cat_low_mmrc(self):
        # CAT alone is sufficient to classify B
        self.assertEqual(self.abe.classify(exac_moderate=0, cat=12, mmrc=0), "B")

    def test_group_b_low_cat_high_mmrc(self):
        # mMRC alone is sufficient to classify B
        self.assertEqual(self.abe.classify(exac_moderate=0, cat=5, mmrc=2), "B")

    # ── Group E ───────────────────────────────────────────────────────────────

    def test_group_e_two_moderate_exac(self):
        self.assertEqual(self.abe.classify(exac_moderate=2, exac_hospitalised=0, cat=5), "E")

    def test_group_e_three_moderate_exac(self):
        self.assertEqual(self.abe.classify(exac_moderate=3, exac_hospitalised=0, cat=5), "E")

    def test_group_e_one_hospitalisation(self):
        self.assertEqual(self.abe.classify(exac_moderate=0, exac_hospitalised=1, cat=5), "E")

    def test_group_e_overrides_high_symptoms(self):
        self.assertEqual(self.abe.classify(exac_moderate=2, exac_hospitalised=0, cat=20), "E")

    def test_group_e_overrides_low_symptoms(self):
        self.assertEqual(self.abe.classify(exac_moderate=2, exac_hospitalised=1, cat=5), "E")

    # ── Defaults and edge cases ───────────────────────────────────────────────

    def test_exac_counts_default_to_zero(self):
        self.assertEqual(self.abe.classify(cat=5), "A")

    def test_e_criterion_without_symptom_data_still_returns_e(self):
        # Group E does not require symptom data
        self.assertEqual(self.abe.classify(exac_moderate=2), "E")

    # ── Missing symptom data ──────────────────────────────────────────────────

    def test_no_symptom_data_returns_na(self):
        self.assertTrue(pd.isna(self.abe.classify(exac_moderate=0, exac_hospitalised=0)))

    def test_non_e_without_symptom_data_returns_na(self):
        self.assertTrue(pd.isna(self.abe.classify(exac_moderate=1)))


if __name__ == "__main__":
    unittest.main()

import unittest
import pandas as pd
from pyspiro import GOLD, STAR, ATS_ERS_2022


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


if __name__ == "__main__":
    unittest.main()

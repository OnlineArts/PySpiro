import unittest

import pandas as pd

from pyspiro import MILLER_2010, KNOX_BROWN_2026


P = MILLER_2010.Parameters


class TestPercentile1(unittest.TestCase):

    def setUp(self):
        self.miller = MILLER_2010()

    def test_male(self):
        self.assertEqual(self.miller.percentile1(P.FEV1Q, 1), 0.50)

    def test_female(self):
        self.assertEqual(self.miller.percentile1(P.FEV1Q, 0), 0.40)

    def test_missing_sex(self):
        self.assertTrue(pd.isna(self.miller.percentile1(P.FEV1Q, None)))

    def test_invalid_sex(self):
        self.assertTrue(pd.isna(self.miller.percentile1(P.FEV1Q, 2)))

    def test_height_indices_have_no_percentile(self):
        # FEV1.Ht^-3 and FEV1.Ht^-2 are not quotients; there is no denominator.
        self.assertTrue(pd.isna(self.miller.percentile1(P.FEV1_HT3, 1)))
        self.assertTrue(pd.isna(self.miller.percentile1(P.FEV1_HT2, 1)))

    def test_matches_knox_brown_2026(self):
        # Knox-Brown et al. independently reproduced Miller's 1st percentiles;
        # the two classes must not drift apart.
        kbq = KNOX_BROWN_2026()
        for sex in (0, 1):
            self.assertEqual(self.miller.percentile1(P.FEV1Q, sex),
                             kbq.percentile1(KNOX_BROWN_2026.Parameters.FEV1, sex))


class TestQuotient(unittest.TestCase):
    """FEV1Q, validated against table 7 of Miller & Pedersen 2010."""

    # (FEV1 L, sex, published FEV1Q) for the paper's four example subjects
    TABLE_7 = [(3.00, 0, 7.50), (0.67, 1, 1.34), (0.67, 0, 1.68), (1.20, 1, 2.40)]

    def setUp(self):
        self.miller = MILLER_2010()

    def test_reproduces_table_7(self):
        for fev1, sex, published in self.TABLE_7:
            self.assertEqual(self.miller.quotient(P.FEV1Q, fev1, sex), published)

    def test_male_and_female_differ_for_the_same_fev1(self):
        self.assertEqual(self.miller.quotient(P.FEV1Q, 1.20, 1), 2.40)
        self.assertEqual(self.miller.quotient(P.FEV1Q, 1.20, 0), 3.00)

    def test_quotient_of_one_at_the_first_percentile(self):
        self.assertEqual(self.miller.quotient(P.FEV1Q, 0.50, 1), 1.00)
        self.assertEqual(self.miller.quotient(P.FEV1Q, 0.40, 0), 1.00)

    def test_below_the_first_percentile(self):
        self.assertEqual(self.miller.quotient(P.FEV1Q, 0.25, 1), 0.50)

    def test_band_is_the_number_of_whole_turnovers(self):
        self.assertEqual(self.miller.band(P.FEV1Q, 1.20, 0), 3)
        self.assertEqual(self.miller.band(P.FEV1Q, 0.25, 1), 0)

    def test_agrees_with_knox_brown_2026(self):
        kbq = KNOX_BROWN_2026()
        for fev1 in (0.30, 0.50, 1.20, 2.50, 4.00):
            for sex in (0, 1):
                self.assertEqual(
                    self.miller.quotient(P.FEV1Q, fev1, sex),
                    kbq.quotient(KNOX_BROWN_2026.Parameters.FEV1, fev1, sex))

    # ── Invalid input ──────────────────────────────────────────────────────

    def test_missing_sex(self):
        self.assertTrue(pd.isna(self.miller.quotient(P.FEV1Q, 1.20, None)))

    def test_none_fev1(self):
        self.assertTrue(pd.isna(self.miller.quotient(P.FEV1Q, None, 1)))

    def test_na_fev1(self):
        self.assertTrue(pd.isna(self.miller.quotient(P.FEV1Q, pd.NA, 1)))

    def test_negative_fev1(self):
        self.assertTrue(pd.isna(self.miller.quotient(P.FEV1Q, -1.0, 1)))

    def test_non_numeric_fev1(self):
        self.assertTrue(pd.isna(self.miller.quotient(P.FEV1Q, "abc", 1)))

    def test_unknown_parameter(self):
        self.assertTrue(pd.isna(self.miller.quotient(99, 1.20, 1)))

    def test_height_index_is_not_a_quotient(self):
        self.assertTrue(pd.isna(self.miller.quotient(P.FEV1_HT3, 1.20, 1)))


class TestHeightStandardised(unittest.TestCase):

    def setUp(self):
        self.miller = MILLER_2010()

    def test_cubed_default(self):
        # 0.67 L / 1.76 m^3 = 0.1229
        self.assertEqual(self.miller.height_standardised(0.67, 176.0), 0.1229)

    def test_squared(self):
        self.assertEqual(self.miller.height_standardised(0.67, 176.0, power=2), 0.2163)

    def test_height_is_taken_in_cm_not_metres(self):
        # Guards the internal cm->m conversion: passing 176 must not give 1.2e-7.
        self.assertGreater(self.miller.height_standardised(0.67, 176.0), 0.01)

    def test_falls_as_height_rises(self):
        tall = self.miller.height_standardised(3.0, 190.0)
        short = self.miller.height_standardised(3.0, 160.0)
        self.assertLess(tall, short)

    def test_cubed_is_smaller_than_squared_above_one_metre(self):
        self.assertLess(self.miller.height_standardised(3.0, 176.0, power=3),
                        self.miller.height_standardised(3.0, 176.0, power=2))

    def test_roughly_a_tenth_of_the_quotient_scale(self):
        # The paper notes the FEV1.Ht^-3 cut-offs are "numerically a tenth" of the
        # FEV1Q ones; this keeps the two indices on their published relative scales.
        for fev1, sex, height in ((3.00, 1, 176.0), (1.20, 0, 163.0), (2.50, 1, 180.0)):
            ratio = (self.miller.height_standardised(fev1, height)
                     / self.miller.quotient(P.FEV1Q, fev1, sex))
            self.assertTrue(0.05 < ratio < 0.15, "ratio %.3f out of range" % ratio)

    # ── Invalid input ──────────────────────────────────────────────────────

    def test_invalid_power(self):
        self.assertTrue(pd.isna(self.miller.height_standardised(3.0, 176.0, power=4)))

    def test_zero_height(self):
        self.assertTrue(pd.isna(self.miller.height_standardised(3.0, 0)))

    def test_negative_height(self):
        self.assertTrue(pd.isna(self.miller.height_standardised(3.0, -176.0)))

    def test_missing_height(self):
        self.assertTrue(pd.isna(self.miller.height_standardised(3.0, None)))

    def test_non_numeric_height(self):
        self.assertTrue(pd.isna(self.miller.height_standardised(3.0, "tall")))

    def test_missing_fev1(self):
        self.assertTrue(pd.isna(self.miller.height_standardised(None, 176.0)))


class TestCompute(unittest.TestCase):

    def setUp(self):
        self.miller = MILLER_2010()
        self.df = pd.DataFrame({
            "sex":    [0, 1, 1],
            "height": [163.0, 176.0, 180.0],
            "FEV1":   [1.20, 0.67, 2.50],
        })

    def test_quotient_column(self):
        result = self.miller.compute(self.df, P.FEV1Q)
        self.assertEqual(list(result.columns), ["FEV1Q"])
        self.assertEqual(result["FEV1Q"].tolist(), [3.00, 1.34, 5.00])

    def test_height_cubed_column(self):
        result = self.miller.compute(self.df, P.FEV1_HT3)
        self.assertEqual(list(result.columns), ["FEV1_HT3"])
        self.assertAlmostEqual(result["FEV1_HT3"].iloc[1], 0.1229, places=4)

    def test_height_squared_column(self):
        result = self.miller.compute(self.df, P.FEV1_HT2)
        self.assertAlmostEqual(result["FEV1_HT2"].iloc[1], 0.2163, places=4)

    def test_index_preserved(self):
        df = self.df.copy()
        df.index = ["a", "b", "c"]
        self.assertEqual(list(self.miller.compute(df, P.FEV1Q).index), ["a", "b", "c"])

    def test_custom_column_names(self):
        df = self.df.rename(columns={"sex": "gender", "FEV1": "fev1_l"})
        result = self.miller.compute(df, P.FEV1Q, value_col="fev1_l", sex_col="gender")
        self.assertEqual(result["FEV1Q"].tolist(), [3.00, 1.34, 5.00])

    def test_height_indices_need_no_sex_column(self):
        df = self.df.drop(columns="sex")
        self.assertFalse(self.miller.compute(df, P.FEV1_HT3, sex_col=None).isna().any().any())

    def test_quotient_needs_a_sex_column(self):
        with self.assertRaises(ValueError):
            self.miller.compute(self.df, P.FEV1Q, sex_col=None)

    def test_height_index_needs_a_height_column(self):
        with self.assertRaises(ValueError):
            self.miller.compute(self.df, P.FEV1_HT3, height_col=None)

    def test_missing_value_col_raises(self):
        with self.assertRaises(ValueError):
            self.miller.compute(self.df, P.FEV1Q, value_col=None)

    def test_unknown_parameter_raises(self):
        with self.assertRaises(ValueError):
            self.miller.compute(self.df, 99)

    def test_integer_parameter_accepted(self):
        result = self.miller.compute(self.df, P.FEV1Q.value)
        self.assertEqual(result["FEV1Q"].tolist(), [3.00, 1.34, 5.00])


class TestScope(unittest.TestCase):
    """Survival prediction is deliberately absent -- see the class docstring."""

    def test_no_survival_api(self):
        miller = MILLER_2010()
        for name in ("survival", "median_survival", "predict_survival",
                     "hazard_ratio", "quartiles"):
            self.assertFalse(hasattr(miller, name),
                             "MILLER_2010 unexpectedly exposes %s()" % name)


if __name__ == "__main__":
    unittest.main()

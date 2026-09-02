import io
import unittest
from contextlib import redirect_stdout

import pandas as pd

from pyspiro import KNOX_BROWN_2026, MILLER_2010, Quotient


IMPLEMENTATIONS = (KNOX_BROWN_2026, MILLER_2010)


class TestSubclassing(unittest.TestCase):

    def test_every_quotient_is_a_quotient_subclass(self):
        for cls in IMPLEMENTATIONS:
            self.assertTrue(issubclass(cls, Quotient), cls.__name__)

    def test_base_class_cannot_be_instantiated(self):
        # compute() is abstract: the batch API differs between papers.
        with self.assertRaises(TypeError):
            Quotient()

    def test_quotients_are_not_reference_equations(self):
        # A quotient has no predicted median, z-score or limit of normal.
        for cls in IMPLEMENTATIONS:
            for absent in ("percent", "zscore", "lms", "lln", "uln"):
                self.assertFalse(hasattr(cls, absent),
                                 "%s unexpectedly exposes %s()" % (cls.__name__, absent))


class TestSharedInterface(unittest.TestCase):

    def test_common_api(self):
        for cls in IMPLEMENTATIONS:
            for name in ("percentile1", "quotient", "band", "compute",
                         "is_sex_specific", "parameter_for", "set_silence"):
                self.assertTrue(callable(getattr(cls, name, None)),
                                "%s is missing %s()" % (cls.__name__, name))

    def test_sex_codes_agree(self):
        for cls in IMPLEMENTATIONS:
            self.assertEqual(cls.Sex.FEMALE.value, 0)
            self.assertEqual(cls.Sex.MALE.value, 1)

    def test_integer_parameters_are_accepted(self):
        self.assertEqual(
            KNOX_BROWN_2026().quotient(KNOX_BROWN_2026.Parameters.FEV1.value, 1.20, 1),
            2.40)
        self.assertEqual(
            MILLER_2010().quotient(MILLER_2010.Parameters.FEV1Q.value, 1.20, 1),
            2.40)

    def test_unknown_parameter_returns_na(self):
        for cls in IMPLEMENTATIONS:
            self.assertTrue(pd.isna(cls().quotient(99, 1.20, 1)), cls.__name__)

    def test_band_is_capped_at_max_band(self):
        for cls, parameter in ((KNOX_BROWN_2026, KNOX_BROWN_2026.Parameters.FEV1),
                               (MILLER_2010, MILLER_2010.Parameters.FEV1Q)):
            self.assertEqual(cls().band(parameter, 99.0, 1), cls.MAX_BAND)


class TestWarnings(unittest.TestCase):

    def test_silent_by_default(self):
        for cls in IMPLEMENTATIONS:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                cls().quotient(99, 1.20, 1)
            self.assertEqual(buffer.getvalue(), "", cls.__name__)

    def test_warning_names_the_concrete_class(self):
        for cls in IMPLEMENTATIONS:
            instance = cls()
            instance.set_silence(False)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                instance.quotient(99, 1.20, 1)
            self.assertIn(cls.__name__, buffer.getvalue())


class TestParameterResolutionByName(unittest.TestCase):
    """parameter_for() bridges an equation's parameter names to a quotient's."""

    def test_exact_name(self):
        self.assertIs(KNOX_BROWN_2026.parameter_for("FEV1"),
                      KNOX_BROWN_2026.Parameters.FEV1)

    def test_q_suffix_fallback(self):
        self.assertIs(MILLER_2010.parameter_for("FEV1"),
                      MILLER_2010.Parameters.FEV1Q)

    def test_unmatched_name(self):
        # GLI_2017 calls the SI transfer factor TLCO; the quotient calls it DLCO_SI.
        self.assertIsNone(KNOX_BROWN_2026.parameter_for("TLCO"))
        self.assertIsNone(MILLER_2010.parameter_for("FVC"))

    def test_missing_name(self):
        self.assertIsNone(KNOX_BROWN_2026.parameter_for(None))


class TestIndependentDerivations(unittest.TestCase):
    """
    The two papers agree on the FEV1 1st percentile, but neither takes its value
    from the other: each declares its own published table.
    """

    def test_neither_class_inherits_from_the_other(self):
        self.assertFalse(issubclass(KNOX_BROWN_2026, MILLER_2010))
        self.assertFalse(issubclass(MILLER_2010, KNOX_BROWN_2026))

    def test_percentiles_are_declared_separately(self):
        miller = MILLER_2010._PERCENTILE_1_BY_SEX[MILLER_2010.Parameters.FEV1Q.value]
        knox = KNOX_BROWN_2026._PERCENTILE_1_BY_SEX[KNOX_BROWN_2026.Parameters.FEV1.value]
        self.assertEqual(miller, knox)
        self.assertIsNot(MILLER_2010._PERCENTILE_1_BY_SEX,
                         KNOX_BROWN_2026._PERCENTILE_1_BY_SEX)


if __name__ == "__main__":
    unittest.main()

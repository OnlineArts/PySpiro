import unittest
import pandas as pd
import numpy as np

from pyspiro import GLI_2012, BOWERMAN_2022, HANKINSON_1999, KUSTER_2008, ECCS_1993
from pyspiro.src.comparison import compare_equations


class TestCompareEquations(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()
        self.bowerman = BOWERMAN_2022()
        self.hankinson = HANKINSON_1999()

    def test_returns_dataframe(self):
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli, self.bowerman]
        )
        self.assertIsInstance(result, pd.DataFrame)

    def test_returns_required_columns(self):
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli, self.bowerman]
        )
        self.assertIn('equation', result.columns)
        self.assertIn('percent_predicted', result.columns)
        self.assertIn('zscore', result.columns)
        self.assertIn('applicable', result.columns)

    def test_patient_as_series(self):
        patient = pd.Series({
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        })
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli, self.bowerman]
        )
        self.assertIsInstance(result, pd.DataFrame)

    def test_missing_required_fields(self):
        patient = {
            'sex': 1,
            'age': 45,
            # missing height
            'ethnicity': 1,
            'FEV1': 2.8
        }
        with self.assertRaises(ValueError):
            compare_equations(
                patient,
                self.gli.Parameters.FEV1,
                equations=[self.gli]
            )

    def test_returns_applicable_flag(self):
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli, self.bowerman]
        )
        # Both should be applicable
        self.assertTrue(result.loc[result['equation'] == 'GLI_2012', 'applicable'].values[0])
        self.assertTrue(result.loc[result['equation'] == 'BOWERMAN_2022', 'applicable'].values[0])

    def test_values_are_numeric(self):
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli]
        )
        pct = result.loc[0, 'percent_predicted']
        z = result.loc[0, 'zscore']
        self.assertTrue(pd.notna(pct))
        self.assertTrue(pd.notna(z))
        self.assertIsInstance(float(pct), float)
        self.assertIsInstance(float(z), float)

    def test_fev1_fvc_comparison(self):
        """FEV1/FVC ratio should work across equations"""
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1FVC': 0.75
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1FVC,
            equations=[self.gli, self.bowerman]
        )
        self.assertEqual(len(result), 2)
        # Both should have valid results for FEV1FVC
        self.assertTrue(result.loc[0, 'applicable'])
        self.assertTrue(result.loc[1, 'applicable'])

    def test_missing_measured_value(self):
        """If measured value column is missing, should mark as not applicable"""
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            # missing FEV1 value
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli]
        )
        self.assertFalse(result.loc[0, 'applicable'])
        self.assertTrue(pd.isna(result.loc[0, 'percent_predicted']))

    def test_out_of_range_age(self):
        """Out of range ages should be marked as not applicable or handled"""
        patient = {
            'sex': 1,
            'age': 2,  # Below GLI_2012 range (3-95)
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli]
        )
        # Result should still have a row, but might not be applicable
        self.assertEqual(len(result), 1)

    def test_different_equations_different_results(self):
        """Different equations should give different %predicted values"""
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,
            equations=[self.gli, self.bowerman]
        )
        pct_gli = result.loc[result['equation'] == 'GLI_2012', 'percent_predicted'].values[0]
        pct_bowerman = result.loc[result['equation'] == 'BOWERMAN_2022', 'percent_predicted'].values[0]
        # Should be different (but both should be reasonable values)
        self.assertNotAlmostEqual(pct_gli, pct_bowerman, places=1)

    def test_parameter_not_in_equation(self):
        """Parameters not in an equation should be marked as not applicable"""
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'RV': 2.0
        }
        result = compare_equations(
            patient,
            self.gli.Parameters.FEV1,  # GL_2012 doesn't have RV
            equations=[self.gli]
        )
        # GLI_2012 should still be in results even if parameter doesn't match
        self.assertEqual(len(result), 1)


class TestCompareEquationsParameterMatching(unittest.TestCase):
    """Regression tests for name-based (not value-based) parameter matching.

    The integer enum values for the same physiological parameter differ across
    equation classes (e.g. value 1 is FEV1 in GLI_2012 but FVC in HANKINSON_1999,
    KUSTER_2008 and ECCS_1993). Matching by value silently compared the wrong
    parameter and marked those equations as not applicable; matching by name
    fixes both problems.
    """

    PATIENT = {
        "sex": 1, "age": 40.0, "height": 175.0, "ethnicity": 1, "FEV1": 3.2,
    }

    def test_misaligned_enum_values_are_applicable(self):
        """Equations whose FEV1 enum value != GLI's must still be applicable."""
        result = compare_equations(
            self.PATIENT,
            GLI_2012.Parameters.FEV1,
            equations=[GLI_2012(), HANKINSON_1999(), KUSTER_2008(), ECCS_1993()],
        )
        for name in ("GLI_2012", "HANKINSON_1999", "KUSTER_2008", "ECCS_1993"):
            applicable = result.loc[result["equation"] == name, "applicable"].values[0]
            self.assertTrue(applicable, f"{name} should be applicable for FEV1")

    def test_matches_direct_call_values(self):
        """%predicted from compare_equations must equal the direct method call."""
        result = compare_equations(
            self.PATIENT,
            GLI_2012.Parameters.FEV1,
            equations=[HANKINSON_1999()],
        )
        pct = float(result.loc[0, "percent_predicted"])
        direct = float(HANKINSON_1999().percent(
            1, 40.0, 175.0, 1, HANKINSON_1999.Parameters.FEV1, 3.2))
        self.assertAlmostEqual(pct, direct, places=4)

    def test_no_silent_wrong_parameter(self):
        """With both FEV1 and FVC present, requesting FEV1 must use FEV1 — not the
        column the misaligned integer value happened to point at (FVC)."""
        patient = dict(self.PATIENT, FVC=5.0)
        result = compare_equations(
            patient,
            GLI_2012.Parameters.FEV1,
            equations=[HANKINSON_1999()],
        )
        pct_fev1 = float(result.loc[0, "percent_predicted"])
        han = HANKINSON_1999()
        expected_fev1 = float(han.percent(1, 40.0, 175.0, 1, han.Parameters.FEV1, 3.2))
        wrong_fvc = float(han.percent(1, 40.0, 175.0, 1, han.Parameters.FVC, 5.0))
        self.assertAlmostEqual(pct_fev1, expected_fev1, places=4)
        self.assertNotAlmostEqual(pct_fev1, wrong_fvc, places=1)


class TestCompareEquationsWithDefaultEquations(unittest.TestCase):

    def test_with_default_equations(self):
        """Test using default equations (None parameter)"""
        patient = {
            'sex': 1,
            'age': 45,
            'height': 175,
            'ethnicity': 1,
            'FEV1': 2.8
        }
        gli = GLI_2012()
        result = compare_equations(
            patient,
            gli.Parameters.FEV1,
            equations=None  # Use defaults
        )
        # Should have multiple equations
        self.assertGreater(len(result), 1)
        # At least GLI_2012 and BOWERMAN_2022 should be present
        equations_names = result['equation'].tolist()
        self.assertIn('GLI_2012', equations_names)
        self.assertIn('BOWERMAN_2022', equations_names)


if __name__ == "__main__":
    unittest.main()

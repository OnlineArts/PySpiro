import unittest
import pandas as pd
import numpy as np

from pyspiro import GLI_2012, BOWERMANN_2022, HANKINSON_1999
from pyspiro.src.comparison import compare_equations


class TestCompareEquations(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()
        self.bowermann = BOWERMANN_2022()
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
            equations=[self.gli, self.bowermann]
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
            equations=[self.gli, self.bowermann]
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
            equations=[self.gli, self.bowermann]
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
            equations=[self.gli, self.bowermann]
        )
        # Both should be applicable
        self.assertTrue(result.loc[result['equation'] == 'GLI_2012', 'applicable'].values[0])
        self.assertTrue(result.loc[result['equation'] == 'BOWERMANN_2022', 'applicable'].values[0])

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
            equations=[self.gli, self.bowermann]
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
            equations=[self.gli, self.bowermann]
        )
        pct_gli = result.loc[result['equation'] == 'GLI_2012', 'percent_predicted'].values[0]
        pct_bowermann = result.loc[result['equation'] == 'BOWERMANN_2022', 'percent_predicted'].values[0]
        # Should be different (but both should be reasonable values)
        self.assertNotAlmostEqual(pct_gli, pct_bowermann, places=1)

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
        # At least GLI_2012 and BOWERMANN_2022 should be present
        equations_names = result['equation'].tolist()
        self.assertIn('GLI_2012', equations_names)
        self.assertIn('BOWERMANN_2022', equations_names)


if __name__ == "__main__":
    unittest.main()

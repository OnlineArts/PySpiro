"""
Tests for compute() on non-LMSReference equation classes.

KUSTER_2008  — polynomial, no LMS; ethnicity in signature but unused.
HANKINSON_1999 — polynomial with derived LMS; ethnicity required and used.
SCHULZ_2013  — direct percentile regression; weight required for lln/uln.

For each equation the compute() result is verified to match row-by-row
scalar calls, covering the same pattern as test_backwards_compat.py but
via the DataFrame API rather than apply(lambda...).
"""

import unittest
import pandas as pd
import numpy as np
from pyspiro import KUSTER_2008, HANKINSON_1999, SCHULZ_2013

M = 1
F = 0


class TestComputeKuster2008(unittest.TestCase):
    """
    KUSTER_2008: ethnicity is in the method signatures for abstract-class
    compliance but is completely ignored in the implementation.
    compute() works without ethnicity_col (defaults to 0 internally).
    """

    def setUp(self):
        self.eq = KUSTER_2008()
        self.df = pd.DataFrame({
            'sex':    [M,    F],
            'age':    [40.0, 55.0],
            'height': [175.0, 163.0],
            'FEV1':   [3.2,   2.1],
        })

    def test_percent_matches_scalar_no_ethnicity_col(self):
        result = self.eq.compute(
            self.df, KUSTER_2008.Parameters.FEV1,
            value_col='FEV1', metrics=('percent',))
        for i, row in self.df.iterrows():
            scalar = self.eq.percent(
                int(row['sex']), float(row['age']), float(row['height']),
                0, KUSTER_2008.Parameters.FEV1, float(row['FEV1']))
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar, places=5)

    def test_lln_matches_scalar(self):
        result = self.eq.compute(
            self.df, KUSTER_2008.Parameters.FEV1_LLN,
            value_col='FEV1', metrics=('lln',))
        for i, row in self.df.iterrows():
            scalar = self.eq.lln(
                int(row['sex']), float(row['age']), float(row['height']),
                0, KUSTER_2008.Parameters.FEV1_LLN, float(row['FEV1']))
            self.assertAlmostEqual(result.loc[i, 'lln'], scalar, places=5)

    def test_explicit_ethnicity_col_also_accepted(self):
        """Supplying an ethnicity column is accepted and has no effect on results."""
        df = self.df.copy()
        df['eth'] = [1, 2]
        r_with    = self.eq.compute(df, KUSTER_2008.Parameters.FEV1,
                                    value_col='FEV1', ethnicity_col='eth',
                                    metrics=('percent',))
        r_without = self.eq.compute(df, KUSTER_2008.Parameters.FEV1,
                                    value_col='FEV1', metrics=('percent',))
        pd.testing.assert_frame_equal(r_with, r_without)

    def test_missing_value_for_percent_raises(self):
        with self.assertRaises(ValueError):
            self.eq.compute(self.df, KUSTER_2008.Parameters.FEV1,
                            metrics=('percent',))

    def test_returns_dataframe_correct_shape(self):
        result = self.eq.compute(
            self.df, KUSTER_2008.Parameters.FEV1,
            value_col='FEV1', metrics=('percent',))
        self.assertEqual(result.shape, (2, 1))
        self.assertIn('percent', result.columns)


class TestComputeHankinson1999(unittest.TestCase):
    """
    HANKINSON_1999: ethnicity is required and used (determines the reference
    table row). ethnicity_col must be supplied; omitting it defaults to
    ethnicity=0 which raises a clear ValueError from the equation itself.
    """

    def setUp(self):
        self.eq = HANKINSON_1999()
        self.df = pd.DataFrame({
            'sex':       [M,    F],
            'age':       [40.0, 55.0],
            'height':    [175.0, 163.0],
            'ethnicity': [1,    1],
            'FVC':       [4.1,  2.8],
        })
        self.param = HANKINSON_1999.Parameters.FVC

    def test_percent_matches_scalar(self):
        result = self.eq.compute(
            self.df, self.param,
            value_col='FVC', ethnicity_col='ethnicity', metrics=('percent',))
        for i, row in self.df.iterrows():
            scalar = self.eq.percent(
                int(row['sex']), float(row['age']), float(row['height']),
                int(row['ethnicity']), self.param, float(row['FVC']))
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar, places=5)

    def test_zscore_matches_scalar(self):
        result = self.eq.compute(
            self.df, self.param,
            value_col='FVC', ethnicity_col='ethnicity', metrics=('zscore',))
        for i, row in self.df.iterrows():
            scalar = self.eq.zscore(
                int(row['sex']), float(row['age']), float(row['height']),
                int(row['ethnicity']), self.param, float(row['FVC']))
            self.assertAlmostEqual(result.loc[i, 'zscore'], scalar, places=5)

    def test_lln_matches_scalar(self):
        result = self.eq.compute(
            self.df, self.param,
            value_col='FVC', ethnicity_col='ethnicity', metrics=('lln',))
        for i, row in self.df.iterrows():
            scalar = self.eq.lln(
                int(row['sex']), float(row['age']), float(row['height']),
                int(row['ethnicity']), self.param, float(row['FVC']))
            self.assertAlmostEqual(result.loc[i, 'lln'], scalar, places=5)

    def test_uln_matches_scalar(self):
        result = self.eq.compute(
            self.df, self.param,
            value_col='FVC', ethnicity_col='ethnicity', metrics=('uln',))
        for i, row in self.df.iterrows():
            scalar = self.eq.uln(
                int(row['sex']), float(row['age']), float(row['height']),
                int(row['ethnicity']), self.param, float(row['FVC']))
            self.assertAlmostEqual(result.loc[i, 'uln'], scalar, places=5)

    def test_all_four_metrics_at_once(self):
        result = self.eq.compute(
            self.df, self.param,
            value_col='FVC', ethnicity_col='ethnicity')
        self.assertEqual(list(result.columns), ['percent', 'zscore', 'lln', 'uln'])
        self.assertFalse(result.isna().any().any())

    def test_omitting_ethnicity_col_raises_at_equation_level(self):
        """Without ethnicity_col the equation receives ethnicity=0, which is
        not a valid Ethnicity value and raises ValueError inside HANKINSON_1999."""
        with self.assertRaises((ValueError, KeyError)):
            self.eq.compute(
                self.df, self.param,
                value_col='FVC', metrics=('percent',)).iloc[0]

    def test_index_preserved(self):
        df = self.df.copy()
        df.index = [100, 200]
        result = self.eq.compute(df, self.param,
                                 value_col='FVC', ethnicity_col='ethnicity',
                                 metrics=('percent',))
        self.assertEqual(list(result.index), [100, 200])

    def test_custom_column_names(self):
        df = self.df.rename(columns={
            'sex': 'gender', 'age': 'age_years',
            'height': 'ht_cm', 'ethnicity': 'eth', 'FVC': 'fvc_meas'})
        result = self.eq.compute(
            df, self.param,
            sex_col='gender', age_col='age_years', height_col='ht_cm',
            value_col='fvc_meas', ethnicity_col='eth', metrics=('percent',))
        scalar = self.eq.percent(M, 40.0, 175.0, 1, self.param, 4.1)
        self.assertAlmostEqual(result.iloc[0]['percent'], scalar, places=5)


class TestComputeSchulz2013(unittest.TestCase):
    """
    SCHULZ_2013: weight_col is required for lln/uln (the only meaningful
    metrics — percent/zscore return None for this equation).
    """

    def setUp(self):
        self.eq = SCHULZ_2013()
        self.df = pd.DataFrame({
            'sex':    [M,    F],
            'age':    [60.0, 65.0],
            'height': [175.0, 163.0],
            'weight': [80.0,  68.0],
            'X10':    [0.10,  0.12],
        })
        self.param = SCHULZ_2013.Parameters.R10

    def test_lln_matches_scalar(self):
        result = self.eq.compute(
            self.df, self.param,
            value_col='X10', weight_col='weight', metrics=('lln',))
        for i, row in self.df.iterrows():
            scalar = self.eq.lln(
                int(row['sex']), float(row['age']), float(row['height']),
                float(row['weight']), self.param, float(row['X10']))
            self.assertAlmostEqual(result.loc[i, 'lln'], scalar, places=5)

    def test_uln_matches_scalar(self):
        result = self.eq.compute(
            self.df, self.param,
            value_col='X10', weight_col='weight', metrics=('uln',))
        for i, row in self.df.iterrows():
            scalar = self.eq.uln(
                int(row['sex']), float(row['age']), float(row['height']),
                float(row['weight']), self.param, float(row['X10']))
            self.assertAlmostEqual(result.loc[i, 'uln'], scalar, places=5)

    def test_lln_and_uln_together(self):
        result = self.eq.compute(
            self.df, self.param,
            weight_col='weight', metrics=('lln', 'uln'))
        self.assertEqual(list(result.columns), ['lln', 'uln'])
        self.assertFalse(result.isna().any().any())

    def test_missing_weight_col_raises(self):
        with self.assertRaises(ValueError):
            self.eq.compute(self.df, self.param, metrics=('lln',))

    def test_custom_column_names(self):
        df = self.df.rename(columns={
            'sex': 'gender', 'weight': 'wt_kg', 'X10': 'r10_ohm'})
        result = self.eq.compute(
            df, self.param,
            sex_col='gender', weight_col='wt_kg',
            value_col='r10_ohm', metrics=('lln',))
        scalar = self.eq.lln(M, 60.0, 175.0, 80.0, self.param, 0.10)
        self.assertAlmostEqual(result.iloc[0]['lln'], scalar, places=5)


if __name__ == '__main__':
    unittest.main()

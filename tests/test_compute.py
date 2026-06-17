"""
Tests for LMSReference.compute(df, ...).

Each test verifies that compute() returns numerically identical results to
calling the scalar methods (percent/zscore/lln/uln) row-by-row, for every
equation that inherits from LMSReference.
"""

import unittest
import pandas as pd
import numpy as np
from pyspiro import (
    GLI_2012,
    BOWERMAN_2022,
    GLI_2017,
    GLI_2021,
    SCAPIS_2023,
    KUBOTA_2014,
)

M = 1
F = 0


def _scalar_row(eq, row, parameter, value_col, with_ethnicity=False):
    """Return (percent, zscore, lln, uln) from four individual scalar calls."""
    if with_ethnicity:
        args = (int(row['sex']), float(row['age']), float(row['height']),
                int(row['ethnicity']), parameter, float(row[value_col]))
    else:
        args = (int(row['sex']), float(row['age']), float(row['height']),
                parameter, float(row[value_col]))
    return (
        eq.percent(*args),
        eq.zscore(*args),
        eq.lln(*args),
        eq.uln(*args),
    )


class TestComputeGLI2012(unittest.TestCase):
    """GLI_2012 has ethnicity in lms() — requires ethnicity column."""

    def setUp(self):
        self.eq = GLI_2012()
        self.df = pd.DataFrame({
            'sex':       [M, F, M],
            'age':       [40.0, 55.0, 30.0],
            'height':    [175.0, 163.0, 180.0],
            'ethnicity': [1, 1, 2],
            'FEV1':      [3.2, 2.1, 3.8],
        })
        self.param = GLI_2012.Parameters.FEV1

    def test_percent_matches_scalar(self):
        result = self.eq.compute(self.df, self.param,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        for i, row in self.df.iterrows():
            scalar, _, _, _ = _scalar_row(self.eq, row, self.param, 'FEV1', with_ethnicity=True)
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar, places=5)

    def test_zscore_matches_scalar(self):
        result = self.eq.compute(self.df, self.param,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        for i, row in self.df.iterrows():
            _, scalar, _, _ = _scalar_row(self.eq, row, self.param, 'FEV1', with_ethnicity=True)
            self.assertAlmostEqual(result.loc[i, 'zscore'], scalar, places=5)

    def test_lln_matches_scalar(self):
        result = self.eq.compute(self.df, self.param,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        for i, row in self.df.iterrows():
            _, _, scalar, _ = _scalar_row(self.eq, row, self.param, 'FEV1', with_ethnicity=True)
            self.assertAlmostEqual(result.loc[i, 'lln'], scalar, places=5)

    def test_uln_matches_scalar(self):
        result = self.eq.compute(self.df, self.param,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        for i, row in self.df.iterrows():
            _, _, _, scalar = _scalar_row(self.eq, row, self.param, 'FEV1', with_ethnicity=True)
            self.assertAlmostEqual(result.loc[i, 'uln'], scalar, places=5)

    def test_returns_dataframe_with_correct_shape(self):
        result = self.eq.compute(self.df, self.param,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, (len(self.df), 4))
        self.assertEqual(list(result.columns), ['percent', 'zscore', 'lln', 'uln'])

    def test_index_preserved(self):
        df = self.df.copy()
        df.index = [10, 20, 30]
        result = self.eq.compute(df, self.param, value_col='FEV1', ethnicity_col='ethnicity')
        self.assertEqual(list(result.index), [10, 20, 30])

    def test_missing_ethnicity_raises(self):
        with self.assertRaises(ValueError):
            self.eq.compute(self.df, self.param, value_col='FEV1')

    def test_partial_metrics(self):
        result = self.eq.compute(self.df, self.param, value_col='FEV1',
                                 ethnicity_col='ethnicity', metrics=('lln', 'uln'))
        self.assertEqual(list(result.columns), ['lln', 'uln'])

    def test_lln_uln_without_value_column(self):
        """lln and uln don't use the measured value — value column is optional for them."""
        result = self.eq.compute(self.df, self.param, ethnicity_col='ethnicity',
                                 metrics=('lln', 'uln'))
        self.assertFalse(result['lln'].isna().any())
        self.assertFalse(result['uln'].isna().any())

    def test_out_of_range_propagates_as_na(self):
        df_oor = self.df.copy()
        df_oor.loc[0, 'age'] = 2.0  # below GLI_2012 minimum age
        result = self.eq.compute(df_oor, self.param,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        self.assertTrue(pd.isna(result.loc[0, 'percent']))
        self.assertFalse(pd.isna(result.loc[1, 'percent']))

    def test_enum_value_and_int_parameter_equivalent(self):
        r_enum = self.eq.compute(self.df, GLI_2012.Parameters.FEV1,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        r_int  = self.eq.compute(self.df, GLI_2012.Parameters.FEV1.value,
                                 value_col='FEV1', ethnicity_col='ethnicity')
        pd.testing.assert_frame_equal(r_enum, r_int)


class TestComputeBowerman2022(unittest.TestCase):
    """BOWERMAN_2022 is race-neutral — no ethnicity argument in lms()."""

    def setUp(self):
        self.eq = BOWERMAN_2022()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 55.0],
            'height': [175.0, 163.0],
            'FVC':    [4.1, 2.8],
        })
        self.param = BOWERMAN_2022.Parameters.FVC

    def test_all_metrics_match_scalar(self):
        result = self.eq.compute(self.df, self.param, value_col='FVC')
        for i, row in self.df.iterrows():
            scalar_pct, scalar_z, scalar_lln, scalar_uln = \
                _scalar_row(self.eq, row, self.param, 'FVC', with_ethnicity=False)
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar_pct, places=5)
            self.assertAlmostEqual(result.loc[i, 'zscore'],  scalar_z,   places=5)
            self.assertAlmostEqual(result.loc[i, 'lln'],     scalar_lln, places=5)
            self.assertAlmostEqual(result.loc[i, 'uln'],     scalar_uln, places=5)

    def test_ethnicity_kwarg_silently_ignored(self):
        """Passing ethnicity to a race-neutral equation is silently ignored."""
        r_with    = self.eq.compute(self.df, self.param, value_col='FVC',
                                    ethnicity_col='nonexistent_col_never_read')
        r_without = self.eq.compute(self.df, self.param, value_col='FVC')
        pd.testing.assert_frame_equal(r_with, r_without)

    def test_missing_value_for_percent_raises(self):
        with self.assertRaises(ValueError):
            self.eq.compute(self.df, self.param, metrics=('percent',))


class TestComputeGLI2017(unittest.TestCase):
    """GLI_2017 — diffusion capacity, no ethnicity."""

    def setUp(self):
        self.eq = GLI_2017()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 55.0],
            'height': [175.0, 163.0],
            'KCO':    [1.5, 1.7],
        })
        self.param = GLI_2017.Parameters.KCO_SI

    def test_lln_uln_match_scalar_no_value_needed(self):
        result = self.eq.compute(self.df, self.param, metrics=('lln', 'uln'))
        for i, row in self.df.iterrows():
            scalar_lln = self.eq.lln(int(row['sex']), float(row['age']),
                                     float(row['height']), self.param, 0.0)
            scalar_uln = self.eq.uln(int(row['sex']), float(row['age']),
                                     float(row['height']), self.param, 0.0)
            self.assertAlmostEqual(result.loc[i, 'lln'], scalar_lln, places=5)
            self.assertAlmostEqual(result.loc[i, 'uln'], scalar_uln, places=5)

    def test_full_metrics_with_value_column(self):
        result = self.eq.compute(self.df, self.param, value_col='KCO')
        for i, row in self.df.iterrows():
            scalar_pct, scalar_z, scalar_lln, scalar_uln = \
                _scalar_row(self.eq, row, self.param, 'KCO', with_ethnicity=False)
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar_pct, places=5)
            self.assertAlmostEqual(result.loc[i, 'zscore'],  scalar_z,   places=5)


class TestComputeGLI2021(unittest.TestCase):
    """GLI_2021 — static lung volumes, no ethnicity."""

    def setUp(self):
        self.eq = GLI_2021()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 55.0],
            'height': [175.0, 163.0],
            'TLC':    [6.5, 5.0],
        })
        self.param = GLI_2021.Parameters.TLC

    def test_all_metrics_match_scalar(self):
        result = self.eq.compute(self.df, self.param, value_col='TLC')
        for i, row in self.df.iterrows():
            scalar_pct, scalar_z, scalar_lln, scalar_uln = \
                _scalar_row(self.eq, row, self.param, 'TLC', with_ethnicity=False)
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar_pct, places=5)
            self.assertAlmostEqual(result.loc[i, 'zscore'],  scalar_z,   places=5)
            self.assertAlmostEqual(result.loc[i, 'lln'],     scalar_lln, places=5)
            self.assertAlmostEqual(result.loc[i, 'uln'],     scalar_uln, places=5)


class TestComputeScapis2023(unittest.TestCase):
    """SCAPIS_2023 — narrow age range 50–65, no ethnicity."""

    def setUp(self):
        self.eq = SCAPIS_2023()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [55.0, 60.0],
            'height': [175.0, 163.0],
            'FEV1':   [3.0, 2.2],
        })
        self.param = SCAPIS_2023.Parameters.pre_BD_FEV1

    def test_all_metrics_match_scalar(self):
        result = self.eq.compute(self.df, self.param, value_col='FEV1')
        for i, row in self.df.iterrows():
            scalar_pct, scalar_z, scalar_lln, scalar_uln = \
                _scalar_row(self.eq, row, self.param, 'FEV1', with_ethnicity=False)
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar_pct, places=5)
            self.assertAlmostEqual(result.loc[i, 'zscore'],  scalar_z,   places=5)
            self.assertAlmostEqual(result.loc[i, 'lln'],     scalar_lln, places=5)
            self.assertAlmostEqual(result.loc[i, 'uln'],     scalar_uln, places=5)


class TestComputeKubota2014(unittest.TestCase):
    """KUBOTA_2014 — Japanese spirometry, no ethnicity."""

    def setUp(self):
        self.eq = KUBOTA_2014()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 55.0],
            'height': [170.0, 158.0],
            'FEV1':   [3.0, 2.0],
        })
        self.param = KUBOTA_2014.Parameters.FEV1

    def test_all_metrics_match_scalar(self):
        result = self.eq.compute(self.df, self.param, value_col='FEV1')
        for i, row in self.df.iterrows():
            scalar_pct, scalar_z, scalar_lln, scalar_uln = \
                _scalar_row(self.eq, row, self.param, 'FEV1', with_ethnicity=False)
            self.assertAlmostEqual(result.loc[i, 'percent'], scalar_pct, places=5)
            self.assertAlmostEqual(result.loc[i, 'zscore'],  scalar_z,   places=5)
            self.assertAlmostEqual(result.loc[i, 'lln'],     scalar_lln, places=5)
            self.assertAlmostEqual(result.loc[i, 'uln'],     scalar_uln, places=5)


class TestComputeNonDefaultColumns(unittest.TestCase):
    """compute() correctly maps non-default column names."""

    def test_custom_column_names(self):
        eq = GLI_2012()
        df = pd.DataFrame({
            'gender':    [M],
            'years':     [40.0],
            'ht_cm':     [175.0],
            'eth':       [1],
            'fev1_meas': [3.2],
        })
        result = eq.compute(
            df, GLI_2012.Parameters.FEV1,
            sex_col='gender', age_col='years', height_col='ht_cm',
            value_col='fev1_meas', ethnicity_col='eth',
        )
        scalar = eq.percent(M, 40.0, 175.0, 1, GLI_2012.Parameters.FEV1, 3.2)
        self.assertAlmostEqual(result.loc[0, 'percent'], scalar, places=5)


if __name__ == '__main__':
    unittest.main()

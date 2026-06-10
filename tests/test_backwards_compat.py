"""
Backwards-compatibility tests for the scalar df.apply(lambda r: eq.method(...)) pattern.

Verifies that users who have not migrated to compute() get identical results
from the old apply(lambda...) approach for every equation.

For LMS-based equations the apply() result is cross-checked against compute().
For non-LMS equations (KUSTER_2008, HANKINSON_1999, SCHULZ_2013) the apply()
result is verified to be finite and consistent with direct scalar calls.
"""

import unittest
import pandas as pd
import numpy as np
from pyspiro import (
    GLI_2012,
    BOWERMANN_2022,
    GLI_2017,
    GLI_2021,
    SCAPIS_2023,
    KUBOTA_2014,
    KUSTER_2008,
    HANKINSON_1999,
    SCHULZ_2013,
)

M = 1
F = 0

# Shared cohort covering LMS equations' overlapping age/height range
_COHORT = pd.DataFrame({
    'sex':       [M,     F,     M],
    'age':       [40.0,  55.0,  30.0],
    'height':    [175.0, 163.0, 180.0],
    'ethnicity': [1,     1,     2],
    'FEV1':      [3.2,   2.1,   3.8],
    'FVC':       [4.1,   2.8,   4.9],
    'FEF75':     [1.0,   0.7,   1.3],
    'KCO':       [1.5,   1.7,   1.4],
    'RV':        [1.8,   1.5,   1.6],
    'TLC':       [6.5,   5.0,   7.0],
})


def _apply_col(df, fn):
    """Return a Series produced by df.apply(fn, axis=1) — the old user pattern."""
    return df.apply(fn, axis=1)


class TestApplyPatternGLI2012(unittest.TestCase):
    """GLI_2012: positional call includes ethnicity between height and parameter."""

    def setUp(self):
        self.eq = GLI_2012()
        self.df = _COHORT.copy()

    def test_percent_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, r.ethnicity,
                GLI_2012.Parameters.FEV1, r.FEV1))
        via_compute = self.eq.compute(
            self.df, GLI_2012.Parameters.FEV1,
            value_col='FEV1', ethnicity_col='ethnicity', metrics=('percent',))['percent']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_zscore_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.zscore(
                r.sex, r.age, r.height, r.ethnicity,
                GLI_2012.Parameters.FEV1, r.FEV1))
        via_compute = self.eq.compute(
            self.df, GLI_2012.Parameters.FEV1,
            value_col='FEV1', ethnicity_col='ethnicity', metrics=('zscore',))['zscore']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_lln_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.lln(
                r.sex, r.age, r.height, r.ethnicity,
                GLI_2012.Parameters.FEV1, r.FEV1))
        via_compute = self.eq.compute(
            self.df, GLI_2012.Parameters.FEV1,
            value_col='FEV1', ethnicity_col='ethnicity', metrics=('lln',))['lln']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_uln_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.uln(
                r.sex, r.age, r.height, r.ethnicity,
                GLI_2012.Parameters.FEV1, r.FEV1))
        via_compute = self.eq.compute(
            self.df, GLI_2012.Parameters.FEV1,
            value_col='FEV1', ethnicity_col='ethnicity', metrics=('uln',))['uln']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_hardcoded_ethnicity_still_accepted(self):
        """Old code that hardcoded ethnicity=1 must still run without error."""
        result = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, 1,
                GLI_2012.Parameters.FEV1, r.FEV1))
        self.assertFalse(result.isna().any())


class TestApplyPatternBowermann2022(unittest.TestCase):
    """BOWERMANN_2022: no ethnicity in the positional call."""

    def setUp(self):
        self.eq = BOWERMANN_2022()
        self.df = _COHORT.copy()

    def test_percent_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height,
                BOWERMANN_2022.Parameters.FVC, r.FVC))
        via_compute = self.eq.compute(
            self.df, BOWERMANN_2022.Parameters.FVC,
            value_col='FVC', metrics=('percent',))['percent']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_zscore_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.zscore(
                r.sex, r.age, r.height,
                BOWERMANN_2022.Parameters.FVC, r.FVC))
        via_compute = self.eq.compute(
            self.df, BOWERMANN_2022.Parameters.FVC,
            value_col='FVC', metrics=('zscore',))['zscore']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


class TestApplyPatternGLI2017(unittest.TestCase):
    """GLI_2017: no ethnicity."""

    def setUp(self):
        self.eq = GLI_2017()
        self.df = _COHORT.copy()

    def test_percent_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height,
                GLI_2017.Parameters.KCO_SI, r.KCO))
        via_compute = self.eq.compute(
            self.df, GLI_2017.Parameters.KCO_SI,
            value_col='KCO', metrics=('percent',))['percent']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


class TestApplyPatternGLI2021(unittest.TestCase):
    """GLI_2021: no ethnicity."""

    def setUp(self):
        self.eq = GLI_2021()
        self.df = _COHORT.copy()

    def test_percent_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height,
                GLI_2021.Parameters.RV, r.RV))
        via_compute = self.eq.compute(
            self.df, GLI_2021.Parameters.RV,
            value_col='RV', metrics=('percent',))['percent']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


class TestApplyPatternScapis2023(unittest.TestCase):
    """SCAPIS_2023: no ethnicity, narrow age range."""

    def setUp(self):
        self.eq = SCAPIS_2023()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [55.0, 60.0],
            'height': [175.0, 163.0],
            'FEV1':   [3.0, 2.2],
        })

    def test_lln_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.lln(
                r.sex, r.age, r.height,
                SCAPIS_2023.Parameters.pre_BD_FEV1, r.FEV1))
        via_compute = self.eq.compute(
            self.df, SCAPIS_2023.Parameters.pre_BD_FEV1,
            value_col='FEV1', metrics=('lln',))['lln']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


class TestApplyPatternKubota2014(unittest.TestCase):
    """KUBOTA_2014: no ethnicity."""

    def setUp(self):
        self.eq = KUBOTA_2014()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 55.0],
            'height': [170.0, 158.0],
            'FEV1':   [3.0, 2.0],
        })

    def test_percent_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height,
                KUBOTA_2014.Parameters.FEV1, r.FEV1))
        via_compute = self.eq.compute(
            self.df, KUBOTA_2014.Parameters.FEV1,
            value_col='FEV1', metrics=('percent',))['percent']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


class TestApplyPatternKuster2008(unittest.TestCase):
    """KUSTER_2008: polynomial — cross-checks apply() against compute() and scalar."""

    def setUp(self):
        self.eq = KUSTER_2008()
        self.df = pd.DataFrame({
            'sex':    [M, F],
            'age':    [40.0, 55.0],
            'height': [175.0, 163.0],
            'FEV1':   [3.2, 2.1],
        })

    def test_percent_apply_produces_finite_values(self):
        result = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, 1,
                KUSTER_2008.Parameters.FEV1, r.FEV1))
        self.assertFalse(result.isna().any())

    def test_lln_apply_produces_finite_values(self):
        result = _apply_col(self.df,
            lambda r: self.eq.lln(
                r.sex, r.age, r.height, 1,
                KUSTER_2008.Parameters.FEV1_LLN, r.FEV1))
        self.assertFalse(result.isna().any())

    def test_apply_matches_direct_scalar_call(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, 1,
                KUSTER_2008.Parameters.FEV1, r.FEV1))
        scalar = self.eq.percent(M, 40.0, 175.0, 1, KUSTER_2008.Parameters.FEV1, 3.2)
        self.assertAlmostEqual(via_apply.iloc[0], scalar, places=5)

    def test_percent_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, 1,
                KUSTER_2008.Parameters.FEV1, r.FEV1))
        via_compute = self.eq.compute(
            self.df, KUSTER_2008.Parameters.FEV1,
            value_col='FEV1', metrics=('percent',))['percent']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_lln_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.lln(
                r.sex, r.age, r.height, 1,
                KUSTER_2008.Parameters.FEV1_LLN, r.FEV1))
        via_compute = self.eq.compute(
            self.df, KUSTER_2008.Parameters.FEV1_LLN,
            value_col='FEV1', metrics=('lln',))['lln']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


class TestApplyPatternHankinson1999(unittest.TestCase):
    """HANKINSON_1999: polynomial — cross-checks apply() against compute() and scalar."""

    def setUp(self):
        self.eq = HANKINSON_1999()
        self.df = pd.DataFrame({
            'sex':       [M,    F],
            'age':       [40.0, 55.0],
            'height':    [175.0, 163.0],
            'ethnicity': [1,    1],
            'FVC':       [4.1,  2.8],
        })

    def test_percent_apply_produces_finite_values(self):
        result = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, r.ethnicity,
                HANKINSON_1999.Parameters.FVC, r.FVC))
        self.assertFalse(result.isna().any())

    def test_apply_matches_direct_scalar_call(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, r.ethnicity,
                HANKINSON_1999.Parameters.FVC, r.FVC))
        scalar = self.eq.percent(M, 40.0, 175.0, 1, HANKINSON_1999.Parameters.FVC, 4.1)
        self.assertAlmostEqual(via_apply.iloc[0], scalar, places=5)

    def test_percent_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.percent(
                r.sex, r.age, r.height, r.ethnicity,
                HANKINSON_1999.Parameters.FVC, r.FVC))
        via_compute = self.eq.compute(
            self.df, HANKINSON_1999.Parameters.FVC,
            value_col='FVC', ethnicity_col='ethnicity', metrics=('percent',))['percent']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_lln_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.lln(
                r.sex, r.age, r.height, r.ethnicity,
                HANKINSON_1999.Parameters.FVC, r.FVC))
        via_compute = self.eq.compute(
            self.df, HANKINSON_1999.Parameters.FVC,
            value_col='FVC', ethnicity_col='ethnicity', metrics=('lln',))['lln']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


class TestApplyPatternSchulz2013(unittest.TestCase):
    """SCHULZ_2013: percentile regression — cross-checks apply() against compute() and scalar."""

    def setUp(self):
        self.eq = SCHULZ_2013()
        self.df = pd.DataFrame({
            'sex':    [M,    F],
            'age':    [60.0, 65.0],
            'height': [175.0, 163.0],
            'weight': [80.0,  68.0],
        })

    def test_percentiles_apply_produces_three_values(self):
        result = self.df.apply(
            lambda r: pd.Series(
                self.eq.percentiles(r.sex, r.age, r.height, r.weight,
                                    SCHULZ_2013.Parameters.R10)),
            axis=1)
        self.assertEqual(result.shape, (2, 3))
        self.assertFalse(result.isna().any().any())

    def test_lln_apply_matches_direct_scalar(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.lln(
                r.sex, r.age, r.height, r.weight,
                SCHULZ_2013.Parameters.R10, None))
        scalar = self.eq.lln(M, 60.0, 175.0, 80.0, SCHULZ_2013.Parameters.R10, None)
        self.assertAlmostEqual(via_apply.iloc[0], scalar, places=5)

    def test_lln_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.lln(
                r.sex, r.age, r.height, r.weight,
                SCHULZ_2013.Parameters.R10, None))
        via_compute = self.eq.compute(
            self.df, SCHULZ_2013.Parameters.R10,
            weight_col='weight', metrics=('lln',))['lln']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)

    def test_uln_apply_matches_compute(self):
        via_apply = _apply_col(self.df,
            lambda r: self.eq.uln(
                r.sex, r.age, r.height, r.weight,
                SCHULZ_2013.Parameters.R10, None))
        via_compute = self.eq.compute(
            self.df, SCHULZ_2013.Parameters.R10,
            weight_col='weight', metrics=('uln',))['uln']
        pd.testing.assert_series_equal(
            via_apply.reset_index(drop=True),
            via_compute.reset_index(drop=True),
            check_names=False)


if __name__ == '__main__':
    unittest.main()

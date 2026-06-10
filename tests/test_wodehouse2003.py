"""
Tests for WODEHOUSE_2003 (nNO classifier for PCD screening).
"""

import sys
import unittest

import pandas

sys.path.insert(0, '/media/veracrypt1/Projekte/PySpiro')
from pyspiro.src.classifiers.WODEHOUSE_2003 import WODEHOUSE_2003


class TestWODEHOUSE2003Classify(unittest.TestCase):

    def setUp(self):
        self.w = WODEHOUSE_2003()

    # ---- PCD range -----------------------------------------------------------

    def test_classify_pcd_range_17ppb(self):
        self.assertEqual(self.w.classify(nno_ppb=17), 'PCD range')

    def test_classify_pcd_range_64ppb(self):
        """PCD group mean from the paper."""
        self.assertEqual(self.w.classify(nno_ppb=64), 'PCD range')

    def test_classify_pcd_range_180ppb(self):
        """Upper end of PCD range in the paper."""
        self.assertEqual(self.w.classify(nno_ppb=180), 'PCD range')

    def test_classify_just_below_cutoff(self):
        self.assertEqual(self.w.classify(nno_ppb=199.9), 'PCD range')

    # ---- Normal range --------------------------------------------------------

    def test_classify_normal_200ppb(self):
        """Exactly at cut-off should be Normal (cut-off is strict <200)."""
        self.assertEqual(self.w.classify(nno_ppb=200), 'Normal')

    def test_classify_normal_543ppb(self):
        """Lower bound of healthy control range from the paper."""
        self.assertEqual(self.w.classify(nno_ppb=543), 'Normal')

    def test_classify_normal_759ppb(self):
        """Healthy control group mean from the paper."""
        self.assertEqual(self.w.classify(nno_ppb=759), 'Normal')

    def test_classify_normal_976ppb(self):
        """Upper bound of healthy control range from the paper."""
        self.assertEqual(self.w.classify(nno_ppb=976), 'Normal')

    def test_classify_normal_1200ppb(self):
        self.assertEqual(self.w.classify(nno_ppb=1200), 'Normal')

    # ---- Constants -----------------------------------------------------------

    def test_cutoff_constant(self):
        self.assertEqual(WODEHOUSE_2003.CUT_OFF, 200)

    def test_normal_mean(self):
        self.assertAlmostEqual(WODEHOUSE_2003.NORMAL_MEAN, 759.1, places=1)

    def test_normal_sd(self):
        self.assertAlmostEqual(WODEHOUSE_2003.NORMAL_SD, 145.8, places=1)

    def test_pcd_mean(self):
        self.assertAlmostEqual(WODEHOUSE_2003.PCD_MEAN, 64.0, places=1)

    def test_pcd_sd(self):
        self.assertAlmostEqual(WODEHOUSE_2003.PCD_SD, 36.6, places=1)

    def test_normal_range(self):
        self.assertEqual(WODEHOUSE_2003.NORMAL_RANGE, (543, 976))

    def test_pcd_range_constant(self):
        self.assertEqual(WODEHOUSE_2003.PCD_RANGE, (17, 180))

    # ---- zscore() ------------------------------------------------------------

    def test_zscore_at_mean_is_zero(self):
        z = self.w.zscore(WODEHOUSE_2003.NORMAL_MEAN)
        self.assertAlmostEqual(z, 0.0, places=10)

    def test_zscore_pcd_mean_strongly_negative(self):
        z = self.w.zscore(WODEHOUSE_2003.PCD_MEAN)
        self.assertLess(z, -4.0)

    def test_zscore_pcd_mean_value(self):
        expected = (64.0 - 759.1) / 145.8
        z = self.w.zscore(64.0)
        self.assertAlmostEqual(z, expected, places=5)

    def test_zscore_minus_one_sd(self):
        z = self.w.zscore(WODEHOUSE_2003.NORMAL_MEAN - WODEHOUSE_2003.NORMAL_SD)
        self.assertAlmostEqual(z, -1.0, places=6)

    def test_zscore_plus_one_sd(self):
        z = self.w.zscore(WODEHOUSE_2003.NORMAL_MEAN + WODEHOUSE_2003.NORMAL_SD)
        self.assertAlmostEqual(z, 1.0, places=6)

    # ---- Error handling ------------------------------------------------------

    def test_missing_kwarg_returns_na(self):
        result = self.w.classify(foo=100)
        self.assertTrue(pandas.isna(result))

    def test_no_args_returns_na(self):
        result = self.w.classify()
        self.assertTrue(pandas.isna(result))

    # ---- Order / metadata ----------------------------------------------------

    def test_order(self):
        self.assertEqual(self.w.get_order(), ['PCD range', 'Normal'])

    def test_float_input(self):
        self.assertEqual(self.w.classify(nno_ppb=150.5), 'PCD range')
        self.assertEqual(self.w.classify(nno_ppb=300.0), 'Normal')


if __name__ == '__main__':
    unittest.main()

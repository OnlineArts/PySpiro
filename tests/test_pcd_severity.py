"""
Tests for PCD_SEVERITY classifier.
"""

import sys
import unittest

sys.path.insert(0, '/media/veracrypt1/Projekte/PySpiro')
from pyspiro.src.classifiers.PCD_SEVERITY import PCD_SEVERITY


class TestPCDSeverityMild(unittest.TestCase):

    def setUp(self):
        self.c = PCD_SEVERITY()

    def test_mild_normal_lci_normal_fev1(self):
        result = self.c.classify(lci_zscore=0.5, fev1_zscore=-0.5)
        self.assertEqual(result, 'Mild')

    def test_mild_lci_at_uln(self):
        """Exactly at ULN threshold is still Mild (threshold is strict >)."""
        result = self.c.classify(lci_zscore=1.645, fev1_zscore=-1.0)
        self.assertEqual(result, 'Mild')

    def test_mild_lci_only_normal(self):
        result = self.c.classify(lci_zscore=1.0)
        self.assertEqual(result, 'Mild')

    def test_mild_fev1_only_normal(self):
        result = self.c.classify(fev1_zscore=-1.0)
        self.assertEqual(result, 'Mild')

    def test_mild_both_normal_low_nno(self):
        result = self.c.classify(lci_zscore=0.5, nno_ppb=50, fev1_zscore=-0.5)
        self.assertEqual(result, 'Mild')


class TestPCDSeverityModerate(unittest.TestCase):

    def setUp(self):
        self.c = PCD_SEVERITY()

    def test_moderate_lci_above_uln(self):
        result = self.c.classify(lci_zscore=2.0)
        self.assertEqual(result, 'Moderate')

    def test_moderate_fev1_below_lln(self):
        result = self.c.classify(fev1_zscore=-2.0)
        self.assertEqual(result, 'Moderate')

    def test_moderate_lci_abnormal_fev1_normal(self):
        result = self.c.classify(lci_zscore=2.5, fev1_zscore=-1.0)
        self.assertEqual(result, 'Moderate')

    def test_moderate_lci_normal_fev1_abnormal(self):
        result = self.c.classify(lci_zscore=1.0, fev1_zscore=-2.0)
        self.assertEqual(result, 'Moderate')

    def test_moderate_just_above_uln(self):
        result = self.c.classify(lci_zscore=1.646)
        self.assertEqual(result, 'Moderate')

    def test_moderate_fev1_just_below_lln(self):
        result = self.c.classify(fev1_zscore=-1.646)
        self.assertEqual(result, 'Moderate')

    def test_moderate_lci_at_severe_boundary(self):
        """LCI z=3.0 exactly is Moderate (threshold is strict >3.0 for Severe)."""
        result = self.c.classify(lci_zscore=3.0)
        self.assertEqual(result, 'Moderate')

    def test_moderate_fev1_at_severe_boundary(self):
        result = self.c.classify(fev1_zscore=-2.5)
        self.assertEqual(result, 'Moderate')


class TestPCDSeveritySevere(unittest.TestCase):

    def setUp(self):
        self.c = PCD_SEVERITY()

    def test_severe_lci_markedly_elevated(self):
        result = self.c.classify(lci_zscore=4.0)
        self.assertEqual(result, 'Severe')

    def test_severe_fev1_markedly_reduced(self):
        result = self.c.classify(fev1_zscore=-3.0)
        self.assertEqual(result, 'Severe')

    def test_severe_both_markedly_abnormal(self):
        result = self.c.classify(lci_zscore=5.0, fev1_zscore=-3.5)
        self.assertEqual(result, 'Severe')

    def test_severe_lci_severe_fev1_normal(self):
        result = self.c.classify(lci_zscore=3.5, fev1_zscore=-1.0)
        self.assertEqual(result, 'Severe')

    def test_severe_lci_normal_fev1_severe(self):
        result = self.c.classify(lci_zscore=0.5, fev1_zscore=-2.6)
        self.assertEqual(result, 'Severe')

    def test_severe_just_above_lci_threshold(self):
        result = self.c.classify(lci_zscore=3.01)
        self.assertEqual(result, 'Severe')

    def test_severe_just_below_fev1_threshold(self):
        result = self.c.classify(fev1_zscore=-2.51)
        self.assertEqual(result, 'Severe')


class TestPCDSeverityInconclusive(unittest.TestCase):

    def setUp(self):
        self.c = PCD_SEVERITY()

    def test_inconclusive_no_data(self):
        result = self.c.classify()
        self.assertEqual(result, 'Inconclusive')

    def test_inconclusive_nno_normal(self):
        """nNO ≥ 200 ppb is inconsistent with PCD."""
        result = self.c.classify(lci_zscore=2.0, nno_ppb=300)
        self.assertEqual(result, 'Inconclusive')

    def test_inconclusive_nno_exactly_at_cutoff(self):
        result = self.c.classify(lci_zscore=2.0, nno_ppb=200)
        self.assertEqual(result, 'Inconclusive')

    def test_inconclusive_nno_healthy_range(self):
        result = self.c.classify(lci_zscore=4.0, nno_ppb=759)
        self.assertEqual(result, 'Inconclusive')

    def test_inconclusive_only_nno_provided(self):
        """nNO alone without LCI or FEV1 cannot grade severity."""
        result = self.c.classify(nno_ppb=80)
        self.assertEqual(result, 'Inconclusive')

    def test_inconclusive_nno_none_no_functional_data(self):
        result = self.c.classify(nno_ppb=None)
        self.assertEqual(result, 'Inconclusive')


class TestPCDSeverityNnoEffect(unittest.TestCase):
    """nNO < 200 ppb should not override severity grading."""

    def setUp(self):
        self.c = PCD_SEVERITY()

    def test_nno_low_does_not_change_mild(self):
        result = self.c.classify(lci_zscore=0.5, nno_ppb=50)
        self.assertEqual(result, 'Mild')

    def test_nno_low_does_not_change_severe(self):
        result = self.c.classify(lci_zscore=4.0, nno_ppb=50)
        self.assertEqual(result, 'Severe')

    def test_nno_none_uses_functional_data(self):
        result = self.c.classify(lci_zscore=2.5, nno_ppb=None)
        self.assertEqual(result, 'Moderate')


class TestPCDSeverityThresholds(unittest.TestCase):

    def test_lci_uln_z_threshold(self):
        self.assertAlmostEqual(PCD_SEVERITY.LCI_ULN_Z, 1.645, places=3)

    def test_lci_severe_z_threshold(self):
        self.assertAlmostEqual(PCD_SEVERITY.LCI_SEVERE_Z, 3.0, places=3)

    def test_fev1_lln_z_threshold(self):
        self.assertAlmostEqual(PCD_SEVERITY.FEV1_LLN_Z, -1.645, places=3)

    def test_fev1_severe_z_threshold(self):
        self.assertAlmostEqual(PCD_SEVERITY.FEV1_SEVERE_Z, -2.5, places=3)

    def test_nno_cutoff(self):
        self.assertEqual(PCD_SEVERITY.NNO_PCD_CUTOFF, 200)

    def test_order(self):
        c = PCD_SEVERITY()
        self.assertEqual(c.get_order(), ['Mild', 'Moderate', 'Severe', 'Inconclusive'])


if __name__ == '__main__':
    unittest.main()

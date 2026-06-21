import pandas as pd

from ..reference import Classifier


class LF_SEVERITY_2022(Classifier):
    """
    Lung function impairment severity grading per ERS/ATS 2022.

    Grades the severity of any lung function impairment (FEV1, FVC, TLC,
    DLCO, etc.) using z-scores relative to the reference population, following
    the 2022 ERS/ATS technical standard (Stanojevic et al. 2022, Table 1).

    Unlike disease-specific staging tools (e.g. GOLD for COPD, GAP for IPF),
    this classifier is parameter-agnostic: it accepts the z-score of any PFT
    measure and returns the corresponding impairment grade.

    Thresholds (Stanojevic et al. 2022, Table 1):
        Normal   : z ≥ −1.645  (at or above the 5th percentile / LLN)
        Mild     : −2.5  ≤ z < −1.645
        Moderate : −4.0  ≤ z < −2.5
        Severe   :        z < −4.0

    For two-sided measures (e.g. lung volumes that may be elevated in
    hyperinflation), the upper limit of normal (ULN, z > +1.645) can be
    flagged separately with flag_uln=True.

    classify() keyword arguments
    ----------------------------
    z        : float — z-score for the parameter to grade
    flag_uln : bool, optional — if True, z > +1.645 returns 'Above ULN'
                                (default False)

    Returns
    -------
    'Normal', 'Mild', 'Moderate', 'Severe', 'Above ULN', or pd.NA on missing input.

    Citation:
        Stanojevic S, Kaminsky DA, Miller MR, et al. ERS/ATS technical standard
        on interpretive strategies for routine lung function tests.
        Eur Respir J. 2022;60(1):2101499. doi: 10.1183/13993003.01499-2021.
    """

    # Boundary z-scores (Table 1, Stanojevic 2022)
    _LLN_Z      = -1.645   # 5th percentile
    _ULN_Z      = +1.645   # 95th percentile
    _MILD_Z     = -2.5
    _MODERATE_Z = -4.0

    NORMAL    = "Normal"
    MILD      = "Mild"
    MODERATE  = "Moderate"
    SEVERE    = "Severe"
    ABOVE_ULN = "Above ULN"

    _order = [NORMAL, MILD, MODERATE, SEVERE]

    def classify(self, **kwargs):
        """Grade lung function impairment severity from a z-score.

        Required kwarg: z (float).
        Optional kwarg: flag_uln (bool, default False).
        Returns a severity label string or pd.NA.
        """
        raw = kwargs.get("z")
        if raw is None:
            return pd.NA
        try:
            z = float(raw)
        except (TypeError, ValueError):
            return pd.NA

        flag_uln = bool(kwargs.get("flag_uln", False))
        if flag_uln and z > self._ULN_Z:
            return self.ABOVE_ULN
        if z >= self._LLN_Z:
            return self.NORMAL
        if z >= self._MILD_Z:
            return self.MILD
        if z >= self._MODERATE_Z:
            return self.MODERATE
        return self.SEVERE

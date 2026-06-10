import pandas as pd

from ..reference import Classifier


class WODEHOUSE_2003(Classifier):
    """
    nNO (nasal nitric oxide) classifier for PCD screening (Wodehouse et al. 2003).

    Classifies nasal NO measurements as consistent with PCD or normal based on
    the threshold established in Wodehouse et al. 2003 (n=10 PCD, n=11 healthy
    controls, n=10 CF, measurement method: breath-hold aspiration at 0.5 L/min).

    Key values from the study:
        PCD:       64 ± 37 ppb  (range 17–180 ppb)
        Controls: 759 ± 146 ppb (range 543–976 ppb)
        CF:       448 ± 163 ppb
        Cut-off:  < 200 ppb → PCD range (100% sensitivity and specificity)

    Note: Reference values for nNO depend on the measurement technique (flow
    rate, breath-hold vs. tidal breathing, nasal vs. oral sampling). These
    values apply specifically to the method described in the citation.

    classify() returns:
        'PCD range'  — nNO < 200 ppb (consistent with PCD)
        'Normal'     — nNO ≥ 200 ppb (inconsistent with PCD)

    zscore() returns the z-score relative to the healthy control distribution.

    Citation:
        Wodehouse T, Kharitonov SA, Mackay IS, Barnes PJ, Durham SR, Scadding GK.
        Nasal nitric oxide measurements for the diagnosis of primary ciliary
        dyskinesia.
        Eur Respir J. 2003;21(1):43–47.
        doi: 10.1183/09031936.03.00027403.
    """

    # Healthy control reference values (ppb)
    NORMAL_MEAN  = 759.1
    NORMAL_SD    = 145.8
    NORMAL_RANGE = (543, 976)

    # PCD group values (ppb)
    PCD_MEAN  = 64.0
    PCD_SD    = 36.6
    PCD_RANGE = (17, 180)

    # Diagnostic cut-off (ppb)
    CUT_OFF = 200

    _order = ['PCD range', 'Normal']

    def classify(self, **kwargs):
        """
        Classify nNO measurement.

        Parameters
        ----------
        nno_ppb : float
            Nasal NO concentration in ppb (parts per billion).

        Returns
        -------
        str : 'PCD range' (< 200 ppb) or 'Normal' (≥ 200 ppb).
        """
        if 'nno_ppb' not in kwargs:
            print("WODEHOUSE_2003: expected nno_ppb as keyword argument.")
            return pd.NA

        nno_ppb = kwargs['nno_ppb']
        if nno_ppb is None or (hasattr(nno_ppb, '__class__') and nno_ppb is pd.NA):
            return pd.NA

        return 'PCD range' if float(nno_ppb) < self.CUT_OFF else 'Normal'

    def zscore(self, nno_ppb: float) -> float:
        """Return z-score of nNO relative to the healthy control distribution."""
        return (float(nno_ppb) - self.NORMAL_MEAN) / self.NORMAL_SD

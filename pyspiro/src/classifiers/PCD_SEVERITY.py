import pandas as pd

from ..reference import Classifier


class PCD_SEVERITY(Classifier):
    """
    PCD severity and disease-monitoring classifier.

    Combines LCI z-score (from RAMSEY_2024), nNO (from WODEHOUSE_2003), and
    FEV1 z-score (from any spirometry reference, e.g. GLI_2012) to grade the
    severity of lung disease in PCD patients.

    Classification logic
    --------------------
    nNO screening (WODEHOUSE_2003 cut-off):
        nNO ≥ 200 ppb → PCD diagnosis is inconsistent → 'Inconclusive'

    LCI z-score thresholds (RAMSEY_2024; ULN = +1.645 z-scores):
        ≤ 1.645  : normal ventilation homogeneity
        > 1.645  : elevated (above ULN) → mild or moderate disease
        > 3.0    : markedly elevated → severe disease

    FEV1 z-score thresholds (LLN = −1.645 z-scores):
        ≥ −1.645 : normal airflow
        < −1.645 : reduced (below LLN) → moderate disease
        < −2.5   : markedly reduced → severe disease

    Combined stages:
        Mild       — LCI ≤ ULN AND FEV1 ≥ LLN (ventilation and airflow preserved)
        Moderate   — LCI > ULN OR FEV1 < LLN (either parameter abnormal)
        Severe     — LCI z > 3.0 OR FEV1 z < −2.5 (either parameter markedly abnormal)
        Inconclusive — nNO ≥ 200 ppb or no data provided

    All input parameters are optional; omit those not measured.  At least one
    of lci_zscore or fev1_zscore is required to produce a non-Inconclusive result.

    Note: nNO reflects ciliary function and is primarily a diagnostic, not a
    severity, marker.  A very low nNO (<77 ppb) confirms ciliary dysfunction
    but does not indicate worse structural lung disease.

    References:
        Ramsey KA et al. Eur Respir J. 2024;63(1):2400524.   (LCI z-score thresholds)
        Wodehouse T et al. Eur Respir J. 2003;21(1):43-47.   (nNO cut-off 200 ppb)
        Gonem S et al. Respir Res. 2014;15:59.               (LCI in bronchiectasis)
    """

    _order = ['Mild', 'Moderate', 'Severe', 'Inconclusive']

    # LCI z-score thresholds (GLI 2024 ULN = 1.64 z-scores)
    LCI_ULN_Z    = 1.645
    LCI_SEVERE_Z = 3.0

    # FEV1 z-score thresholds (standard ATS/ERS LLN = −1.645)
    FEV1_LLN_Z    = -1.645
    FEV1_SEVERE_Z = -2.5

    # nNO diagnostic cut-off (ppb, Wodehouse 2003)
    NNO_PCD_CUTOFF = 200

    def classify(self, **kwargs):
        """
        Classify PCD disease severity.

        Parameters
        ----------
        lci_zscore  : float, optional
            LCI z-score computed via RAMSEY_2024.
        nno_ppb     : float, optional
            Nasal NO in ppb (breath-hold aspiration method, Wodehouse 2003).
        fev1_zscore : float, optional
            FEV1 z-score from any spirometry reference equation.

        Returns
        -------
        str : 'Mild', 'Moderate', 'Severe', or 'Inconclusive'.
        """
        lci_zscore  = kwargs.get('lci_zscore',  None)
        nno_ppb     = kwargs.get('nno_ppb',     None)
        fev1_zscore = kwargs.get('fev1_zscore', None)

        if lci_zscore is None and fev1_zscore is None:
            return 'Inconclusive'

        if nno_ppb is not None and float(nno_ppb) >= self.NNO_PCD_CUTOFF:
            return 'Inconclusive'

        lci_severe   = lci_zscore  is not None and float(lci_zscore)  > self.LCI_SEVERE_Z
        fev1_severe  = fev1_zscore is not None and float(fev1_zscore) < self.FEV1_SEVERE_Z
        lci_abnormal = lci_zscore  is not None and float(lci_zscore)  > self.LCI_ULN_Z
        fev1_abnormal = fev1_zscore is not None and float(fev1_zscore) < self.FEV1_LLN_Z

        if lci_severe or fev1_severe:
            return 'Severe'
        if lci_abnormal or fev1_abnormal:
            return 'Moderate'
        return 'Mild'

import pandas as pd

from ..reference import Classifier


class BDR_2022(Classifier):
    """
    Bronchodilator response (BDR) classifier per ERS/ATS 2022.

    A positive BDR is defined as an increase in FEV1 or FVC of >10% of the
    predicted value following bronchodilator administration.

    Unlike the 2005 ATS/ERS criterion (≥12% relative + ≥200 mL absolute),
    the 2022 standard expresses BDR relative to the predicted value, removing
    the dependence on baseline lung function level, sex, and height.

    Formula: change (%) = (post_BD − pre_BD) / predicted × 100
    Threshold: > 10% of predicted → positive response.

    classify() keyword arguments
    ----------------------------
    pre_fev1       : float — pre-BD FEV1 (litres)
    post_fev1      : float — post-BD FEV1 (litres)
    predicted_fev1 : float — predicted FEV1 from a reference equation
    pre_fvc        : float — pre-BD FVC (litres)
    post_fvc       : float — post-BD FVC (litres)
    predicted_fvc  : float — predicted FVC from a reference equation

    At least one complete set (pre/post/predicted for FEV1 or FVC) must be
    supplied. Partial sets for a parameter are ignored with pd.NA.

    Returns
    -------
    'Positive (FEV1 and FVC)' — both FEV1 and FVC criteria met
    'Positive (FEV1)'         — FEV1 criterion met, FVC not or not assessed
    'Positive (FVC)'          — FVC criterion met, FEV1 not or not assessed
    'Negative'                — neither criterion met
    pd.NA                     — no complete parameter set supplied

    Citation:
        Stanojevic S, Kaminsky DA, Miller MR, et al. ERS/ATS technical standard
        on interpretive strategies for routine lung function tests.
        Eur Respir J. 2022;60(1):2101499. doi: 10.1183/13993003.01499-2021.
    """

    THRESHOLD = 10.0  # % of predicted

    POSITIVE_BOTH = "Positive (FEV1 and FVC)"
    POSITIVE_FEV1 = "Positive (FEV1)"
    POSITIVE_FVC  = "Positive (FVC)"
    NEGATIVE      = "Negative"

    _order = [POSITIVE_BOTH, POSITIVE_FEV1, POSITIVE_FVC, NEGATIVE]

    @staticmethod
    def _change_pct(pre, post, predicted):
        """Return (post - pre) / predicted * 100, or None on invalid inputs."""
        try:
            pre, post, pred = float(pre), float(post), float(predicted)
            if pred <= 0:
                return None
            return (post - pre) / pred * 100.0
        except (TypeError, ValueError):
            return None

    def classify(self, **kwargs):
        """Classify BDR for FEV1 and/or FVC.

        Returns a result string or pd.NA if no complete parameter set is given.
        """
        fev1_pos = None
        fvc_pos  = None

        pre_f1  = kwargs.get("pre_fev1")
        post_f1 = kwargs.get("post_fev1")
        pred_f1 = kwargs.get("predicted_fev1")
        if all(v is not None for v in (pre_f1, post_f1, pred_f1)):
            chg = self._change_pct(pre_f1, post_f1, pred_f1)
            if chg is not None:
                fev1_pos = chg > self.THRESHOLD

        pre_fv  = kwargs.get("pre_fvc")
        post_fv = kwargs.get("post_fvc")
        pred_fv = kwargs.get("predicted_fvc")
        if all(v is not None for v in (pre_fv, post_fv, pred_fv)):
            chg = self._change_pct(pre_fv, post_fv, pred_fv)
            if chg is not None:
                fvc_pos = chg > self.THRESHOLD

        if fev1_pos is None and fvc_pos is None:
            return pd.NA

        if fev1_pos and fvc_pos:
            return self.POSITIVE_BOTH
        if fev1_pos:
            return self.POSITIVE_FEV1
        if fvc_pos:
            return self.POSITIVE_FVC
        return self.NEGATIVE

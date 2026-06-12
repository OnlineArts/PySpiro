import pandas as pd

from ..reference import Classifier


class GOLD_ABE(Classifier):
    """
    GOLD 2023 ABE group assignment for COPD.

    Replaces the previous ABCD tool. Groups patients into three categories
    based on exacerbation history and symptom burden. The ABE assessment is
    applied after spirometric confirmation of airflow obstruction (FEV1/FVC
    < LLN or < 0.70 post-BD) and independently of GOLD spirometric stage
    (I–IV).

    Groups:
        A — Low symptom burden AND low exacerbation risk
            Symptoms:       CAT < 10 OR mMRC 0–1
            Exacerbations:  ≤1 moderate (not leading to hospitalisation)
                            in the past 12 months; no hospitalisation

        B — High symptom burden AND low exacerbation risk
            Symptoms:       CAT ≥ 10 OR mMRC ≥ 2
            Exacerbations:  ≤1 moderate (not leading to hospitalisation)
                            in the past 12 months; no hospitalisation

        E — High exacerbation risk (regardless of symptoms)
            Exacerbations:  ≥2 moderate exacerbations OR
                            ≥1 exacerbation requiring hospitalisation
                            in the past 12 months

    Exacerbation risk (E) is evaluated first; symptom burden (A vs B) is
    evaluated only when the patient does not meet the E criterion.

    classify() keyword arguments
    ----------------------------
    exac_moderate      : int  — number of moderate exacerbations in past 12 months
                                (not requiring hospitalisation)
    exac_hospitalised  : int  — number of exacerbation-related hospitalisations
                                in past 12 months
    cat                : int  — COPD Assessment Test score (0–40); optional if
                                mmrc is supplied
    mmrc               : int  — mMRC dyspnoea scale (0–4); optional if cat is supplied

    At least one of cat or mmrc must be supplied to assign A vs B.
    If neither is supplied and the patient does not meet criterion E,
    returns pd.NA.

    Returns
    -------
    'A', 'B', 'E', or pd.NA.

    Citation:
        Global Initiative for Chronic Obstructive Lung Disease (GOLD).
        Global Strategy for the Diagnosis, Management, and Prevention of COPD.
        2023 Report. www.goldcopd.org.
    """

    _order = ["A", "B", "E"]

    # Thresholds
    _CAT_HIGH  = 10   # CAT ≥ 10 → high symptom burden
    _MMRC_HIGH = 2    # mMRC ≥ 2 → high symptom burden
    _EXAC_E    = 2    # ≥2 moderate exacerbations → group E

    def classify(self, **kwargs):
        """Assign GOLD ABE group.

        Returns 'A', 'B', 'E', or pd.NA on insufficient input.
        """
        exac_mod  = kwargs.get("exac_moderate",     0)
        exac_hosp = kwargs.get("exac_hospitalised",  0)
        cat       = kwargs.get("cat",   None)
        mmrc      = kwargs.get("mmrc",  None)

        try:
            exac_mod  = int(exac_mod)
            exac_hosp = int(exac_hosp)
        except (TypeError, ValueError):
            return pd.NA

        # E criterion: ≥2 moderate OR ≥1 hospitalised
        if exac_mod >= self._EXAC_E or exac_hosp >= 1:
            return "E"

        # Symptom burden for A vs B
        high_symptoms = None

        if cat is not None:
            try:
                high_symptoms = int(cat) >= self._CAT_HIGH
            except (TypeError, ValueError):
                pass

        if mmrc is not None:
            try:
                mmrc_high = int(mmrc) >= self._MMRC_HIGH
                # Either instrument alone is sufficient; OR logic per GOLD 2023
                high_symptoms = high_symptoms or mmrc_high if high_symptoms is not None else mmrc_high
            except (TypeError, ValueError):
                pass

        if high_symptoms is None:
            return pd.NA

        return "B" if high_symptoms else "A"

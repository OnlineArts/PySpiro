import pandas as pd

from ..reference import Classifier

class GOLD(Classifier):
    """
    GOLD spirometric severity classifier for COPD (GOLD 2023).

    Classifies airflow obstruction into four stages based on FEV1 % predicted
    in patients with a confirmed obstructive pattern (FEV1/FVC < 0.70 post-BD).

    Stages:
        1 (Mild)        — FEV1 >= 80% predicted
        2 (Moderate)    — 50% <= FEV1 < 80% predicted
        3 (Severe)      — 30% <= FEV1 < 50% predicted
        4 (Very severe) — FEV1 < 30% predicted

    Input: FEV1 % predicted as FEV1p (accepts both 0-1 and 0-100 notation).

    Citation:
        Global Initiative for Chronic Obstructive Lung Disease (GOLD).
        Global Strategy for the Diagnosis, Management, and Prevention of COPD.
        2023 Report. www.goldcopd.org.
    """

    _order = [1, 2, 3, 4]
    _map_names = {1: "I", 2: "II", 3: "III", 4: "IV"}
    _map_meaning = {1: "mild", 2: "moderate", 3: "severe", 4: "very severe"}

    def classify(self, **kwargs):
        """Return GOLD stage (1-4) for the given FEV1 % predicted (FEV1p)."""

        if len(kwargs) == 1:
            if "FEV1p" in kwargs:
                fev1 = kwargs["FEV1p"]
            else:
                print("GOLD Classifier: expected FEV1p as keyword argument.")
                return pd.NA
        else:
            print("GOLD Classifier: Ambiguous number of arguments, GOLD expects only FEV1%predicted as FEV1p variable")
            return pd.NA

        # Accept both fraction (0-1) and percentage (0-100) notation
        if fev1 <= 1:
            fev1 = fev1 * 100

        if fev1 >= 80:
            return 1
        elif 50 <= fev1 < 80:
            return 2
        elif 30 <= fev1 < 50:
            return 3
        elif fev1 < 30:
            return 4

        return pd.NA

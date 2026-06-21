import pandas as pd

from ..reference import Classifier

class STAR(Classifier):
    """
    STAR spirometric severity classifier based on FEV1/FVC ratio.

    Classifies airflow obstruction into four stages using the FEV1/FVC ratio
    directly, rather than FEV1 % predicted. Returns pd.NA for non-obstructive
    patterns (FEV1/FVC >= 70%).

    Stages:
        1 (Mild)        — 60% <= FEV1/FVC < 70%
        2 (Moderate)    — 50% <= FEV1/FVC < 60%
        3 (Severe)      — 40% <= FEV1/FVC < 50%
        4 (Very severe) — FEV1/FVC < 40%

    Input: FEV1/FVC as FEV1_FVC (ratio), or FEV1 and FVC separately.
    Accepts both 0-1 and 0-100 notation.

    Citation:
        Bhatt SP, Nakhmani A, Fortis S, Strand MJ, Silverman EK, Sciurba FC, Bodduluri S.
        FEV1/FVC Severity Stages for Chronic Obstructive Pulmonary Disease Get access Arrow
        Am J Respir Crit Care Med. 2023 Sep 15;208(6):676-684
        doi: 10.1164/rccm.202303-0450OC.
    """

    _order = [1, 2, 3, 4]

    def classify(self, **kwargs):
        """Return STAR stage (1-4) for the given FEV1/FVC ratio, or pd.NA if not obstructive."""

        if len(kwargs) == 1:
            if "FEV1_FVC" in kwargs:
                fev1_fvc = kwargs["FEV1_FVC"]
            else:
                print("STAR Classifier: Identified only one argument, assuming FEV1/FVC")
                fev1_fvc = next(iter(kwargs.values()))
        elif len(kwargs) == 2:
            if "FEV1" in kwargs and "FVC" in kwargs:
                fev1_fvc = kwargs["FEV1"] / kwargs["FVC"]
            else:
                print("STAR Classifier: Identified two arguments, assuming first one is FEV1%pred and second FVC%pred")
                vals = list(kwargs.values())
                fev1_fvc = vals[0] / vals[1]
        else:
            print("STAR Classifier: Ambiguous number of arguments, STAR expects FEV1/FVC or both variable separately")
            return pd.NA

        # Accept both fraction (0-1) and percentage (0-100) notation
        if fev1_fvc <= 1:
            fev1_fvc = fev1_fvc * 100

        if fev1_fvc >= 70:
            return pd.NA
        elif 60 <= fev1_fvc < 70:
            return 1
        elif 50 <= fev1_fvc < 60:
            return 2
        elif 40 <= fev1_fvc < 50:
            return 3
        elif fev1_fvc < 40:
            return 4

        return pd.NA

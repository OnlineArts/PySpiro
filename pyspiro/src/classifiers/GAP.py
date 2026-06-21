import pandas as pd

from ..reference import Classifier


class GAP(Classifier):
    """
    GAP index and staging system for idiopathic pulmonary fibrosis (IPF).

    A validated point-score model predicting 1-, 2-, and 3-year mortality in
    IPF patients using gender, age, and two physiological variables (FVC and
    DLCO). Higher scores indicate greater mortality risk.

    Scoring (Figure 2, Ley et al. 2012)
    ------------------------------------
    G — Gender
        Female → 0 points
        Male   → 1 point

    A — Age (years)
        ≤60    → 0 points
        61–65  → 1 point
        >65    → 2 points

    P — Physiology (FVC % predicted + DLCO % predicted)

        FVC % predicted:
            >75  → 0 points
            50–75 → 1 point
            <50  → 2 points

        DLCO % predicted:
            >55  → 0 points
            36–55 → 1 point
            ≤35  → 2 points
            Cannot perform → 3 points

    Total GAP score: 0–8 points.

    Staging (Table 3, Ley et al. 2012):
        Stage I   (0–3 points): 1-y 5.6%, 2-y 10.9%, 3-y 16.3% mortality
        Stage II  (4–5 points): 1-y 16.2%, 2-y 29.9%, 3-y 42.1% mortality
        Stage III (6–8 points): 1-y 39.2%, 2-y 62.1%, 3-y 76.8% mortality

    score() returns the raw 0–8 GAP score.
    classify() returns the stage ('I', 'II', or 'III').

    classify() and score() keyword arguments
    ----------------------------------------
    sex        : int   — 0 = female, 1 = male
    age        : float — age in years
    fvc_pct    : float — FVC % predicted (0–100 scale)
    dlco_pct   : float — DLCO % predicted (0–100 scale); pass None if patient
                         cannot perform the DLCO manoeuvre
    dlco_na    : bool  — alternative way to indicate DLCO cannot be performed;
                         if True, dlco_pct is ignored (default False)

    Citation:
        Ley B, Ryerson CJ, Vittinghoff E, et al. A multidimensional index and
        staging system for idiopathic pulmonary fibrosis. Ann Intern Med.
        2012;156(10):684-91. doi: 10.7326/0003-4819-156-10-201205150-00004.
    """

    _order = ["I", "II", "III"]

    # Predicted mortality by stage (1-y, 2-y, 3-y) from Ley 2012 Table 3
    MORTALITY = {
        "I":   {"1y": 0.056, "2y": 0.109, "3y": 0.163},
        "II":  {"1y": 0.162, "2y": 0.299, "3y": 0.421},
        "III": {"1y": 0.392, "2y": 0.621, "3y": 0.768},
    }

    @staticmethod
    def _points_gender(sex):
        return int(sex == 1)  # male = 1

    @staticmethod
    def _points_age(age):
        if age <= 60:
            return 0
        if age <= 65:
            return 1
        return 2

    @staticmethod
    def _points_fvc(fvc_pct):
        if fvc_pct > 75:
            return 0
        if fvc_pct >= 50:
            return 1
        return 2

    @staticmethod
    def _points_dlco(dlco_pct, dlco_na):
        if dlco_na:
            return 3
        if dlco_pct is None:
            return 3
        if dlco_pct > 55:
            return 0
        if dlco_pct > 35:
            return 1
        return 2

    def _parse_inputs(self, kwargs):
        try:
            sex     = int(kwargs["sex"])
            age     = float(kwargs["age"])
            fvc_pct = float(kwargs["fvc_pct"])
        except KeyError as e:
            raise ValueError(f"GAP: missing required argument {e}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"GAP: invalid argument — {e}") from e

        dlco_na  = bool(kwargs.get("dlco_na", False))
        dlco_raw = kwargs.get("dlco_pct", None)
        dlco_pct = None
        if not dlco_na and dlco_raw is not None:
            try:
                dlco_pct = float(dlco_raw)
            except (TypeError, ValueError):
                dlco_na = True  # treat as cannot perform

        return sex, age, fvc_pct, dlco_pct, dlco_na

    def score(self, **kwargs):
        """Return the raw GAP score (0–8) or pd.NA on invalid input."""
        try:
            sex, age, fvc_pct, dlco_pct, dlco_na = self._parse_inputs(kwargs)
        except ValueError:
            return pd.NA
        return (self._points_gender(sex) + self._points_age(age)
                + self._points_fvc(fvc_pct) + self._points_dlco(dlco_pct, dlco_na))

    def classify(self, **kwargs):
        """Return the GAP stage ('I', 'II', or 'III') or pd.NA on invalid input."""
        s = self.score(**kwargs)
        if pd.isna(s):
            return pd.NA
        if s <= 3:
            return "I"
        if s <= 5:
            return "II"
        return "III"

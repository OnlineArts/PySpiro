import pandas as pd

from ..reference import Classifier


class BODE(Classifier):
    """
    BODE index for COPD — multidimensional mortality predictor.

    A 10-point scale combining four independent predictors of all-cause and
    respiratory mortality in COPD patients. Higher scores indicate greater
    risk of death.

    Scoring (Table 2, Celli et al. 2004)
    -------------------------------------
    B — Body-mass index (kg/m²)
        >21  → 0 points
        ≤21  → 1 point

    O — Airflow obstruction: FEV1 % predicted (post-bronchodilator)
        ≥65  → 0 points
        50–64 → 1 point
        36–49 → 2 points
        ≤35  → 3 points

    D — Dyspnoea: modified Medical Research Council (mMRC) scale (0–4)
        0–1  → 0 points
        2    → 1 point
        3    → 2 points
        4    → 3 points

    E — Exercise capacity: six-minute walk test distance (metres)
        ≥350  → 0 points
        250–349 → 1 point
        150–249 → 2 points
        ≤149  → 3 points

    Total BODE score: 0–10 points.

    Mortality quartiles (original paper):
        Quartile 1: 0–2
        Quartile 2: 3–4
        Quartile 3: 5–6
        Quartile 4: 7–10

    score() returns the raw 0–10 BODE score.
    classify() returns the quartile (1–4).

    classify() and score() keyword arguments
    ----------------------------------------
    bmi       : float — body-mass index (kg/m²)
    fev1p     : float — post-BD FEV1 % predicted (0–100 scale)
    mmrc      : int   — mMRC dyspnoea score (0–4)
    walk6m    : float — six-minute walk distance (metres)

    All four arguments are required. Returns pd.NA if any is missing or invalid.

    Citation:
        Celli BR, Cote CG, Marin JM, et al. The body-mass index, airflow
        obstruction, dyspnea, and exercise capacity index in chronic obstructive
        pulmonary disease. N Engl J Med. 2004;350(10):1005-12.
        doi: 10.1056/NEJMoa021322.
    """

    _order = [1, 2, 3, 4]

    @staticmethod
    def _points_bmi(bmi):
        return 1 if bmi <= 21 else 0

    @staticmethod
    def _points_fev1(fev1p):
        # Accept 0-1 fraction notation
        if fev1p <= 1:
            fev1p = fev1p * 100
        if fev1p >= 65:
            return 0
        if fev1p >= 50:
            return 1
        if fev1p >= 36:
            return 2
        return 3

    @staticmethod
    def _points_mmrc(mmrc):
        if mmrc <= 1:
            return 0
        if mmrc == 2:
            return 1
        if mmrc == 3:
            return 2
        return 3  # mmrc == 4

    @staticmethod
    def _points_walk(walk6m):
        if walk6m >= 350:
            return 0
        if walk6m >= 250:
            return 1
        if walk6m >= 150:
            return 2
        return 3

    def _parse_inputs(self, kwargs):
        """Return (bmi, fev1p, mmrc, walk6m) floats or raise ValueError."""
        try:
            bmi    = float(kwargs["bmi"])
            fev1p  = float(kwargs["fev1p"])
            mmrc   = int(kwargs["mmrc"])
            walk6m = float(kwargs["walk6m"])
        except KeyError as e:
            raise ValueError(f"BODE: missing required argument {e}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"BODE: invalid argument — {e}") from e
        if not (0 <= mmrc <= 4):
            raise ValueError(f"BODE: mMRC must be 0–4, got {mmrc}")
        return bmi, fev1p, mmrc, walk6m

    def score(self, **kwargs):
        """Return the raw BODE score (0–10) or pd.NA on invalid input."""
        try:
            bmi, fev1p, mmrc, walk6m = self._parse_inputs(kwargs)
        except ValueError:
            return pd.NA
        return (self._points_bmi(bmi) + self._points_fev1(fev1p)
                + self._points_mmrc(mmrc) + self._points_walk(walk6m))

    def classify(self, **kwargs):
        """Return the BODE quartile (1–4) or pd.NA on invalid input."""
        s = self.score(**kwargs)
        if pd.isna(s):
            return pd.NA
        if s <= 2:
            return 1
        if s <= 4:
            return 2
        if s <= 6:
            return 3
        return 4

import pandas as pd

from ..reference import Classifier


class ECOPD_ROME_2021(Classifier):
    """
    Rome Proposal severity classification for COPD exacerbations (ECOPDs).

    Classifies an acute COPD exacerbation into Mild, Moderate, or Severe based
    on six objectively measured variables agreed by an international expert panel
    using a modified Delphi methodology.

    Classification logic
    --------------------
    **Severe** (evaluated first):
        Arterial blood gas shows BOTH hypercapnia AND respiratory acidosis:
            PaCO2 > 45 mmHg AND pH < 7.35

    **Moderate** (evaluated next):
        At least 3 of 5 primary parameters exceed the mild threshold:
            1. Dyspnea VAS ≥ 5 (scale 0–10)
            2. Respiratory rate ≥ 24 breaths/min
            3. Heart rate ≥ 95 bpm
            4. Resting SaO2 < 92% (ambient air) AND/OR change from baseline > 3%
            5. CRP ≥ 10 mg/L

    **Mild** (default):
        Fewer than 3 of 5 primary parameters are abnormal.

    Parameter notes
    ---------------
    - Parameters not supplied (None / pd.NA) are excluded from the count.
      A minimum of 3 provided primary parameters is required for Moderate
      classification; otherwise Mild is returned when ABG criteria are not met.
    - SaO2 and sao2_change together represent one of the five primary parameters.
      The criterion is met if either (or both) are in the moderate range.
    - CRP is optional ("if obtained"). Omitting it reduces the available count
      to 4 parameters.
    - Severe requires both paco2 and ph to be provided; if either is absent the
      severe criterion cannot be evaluated and the result falls back to
      Mild/Moderate based on primary parameters.

    classify() keyword arguments
    ----------------------------
    dyspnea_vas  : float  — Dyspnea visual analog scale (0–10); moderate ≥ 5
    rr           : float  — Respiratory rate (breaths/min); moderate ≥ 24
    hr           : float  — Heart rate (bpm); moderate ≥ 95
    sao2         : float  — Resting SpO2 / SaO2 (%); moderate < 92
    sao2_change  : float  — Absolute reduction from baseline (%); moderate > 3
    crp          : float  — Serum C-reactive protein (mg/L); moderate ≥ 10
    paco2        : float  — Arterial PaCO2 (mmHg); severe > 45
    ph           : float  — Arterial pH; severe < 7.35

    All arguments are optional; pass None or omit to indicate "not measured".

    Returns
    -------
    'Mild', 'Moderate', 'Severe', or pd.NA (when no parameters are supplied).

    score() returns a dict with keys 'abnormal_count', 'n_assessed', and
    'severe_abg' for transparency.

    Citation:
        Celli BR, Fabbri LM, Aaron SD, et al. An Updated Definition and
        Severity Classification of Chronic Obstructive Pulmonary Disease
        Exacerbations: The Rome Proposal. Am J Respir Crit Care Med.
        2021;204(11):1251-1258. doi: 10.1164/rccm.202108-1819PP
    """

    _order = ["Mild", "Moderate", "Severe"]

    # Thresholds
    _VAS_MODERATE   = 5      # VAS ≥ 5 → moderate
    _RR_MODERATE    = 24     # RR ≥ 24 breaths/min → moderate
    _HR_MODERATE    = 95     # HR ≥ 95 bpm → moderate
    _SAO2_MODERATE  = 92     # SaO2 < 92 % → moderate
    _SAO2_DELTA_MOD = 3      # change > 3 % → moderate
    _CRP_MODERATE   = 10     # CRP ≥ 10 mg/L → moderate
    _PACO2_SEVERE   = 45     # PaCO2 > 45 mmHg → severe (with acidosis)
    _PH_SEVERE      = 7.35   # pH < 7.35 → severe (with hypercapnia)
    _MODERATE_THRESHOLD = 3  # ≥3 abnormal primary parameters → Moderate

    @staticmethod
    def _to_float(val):
        """Return float or None if val is missing/invalid."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    def score(self, **kwargs):
        """
        Return a dict summarising the Rome scoring:
            'abnormal_count' : int  — number of abnormal primary parameters
            'n_assessed'     : int  — number of primary parameters provided
            'severe_abg'     : bool — True if ABG meets severe criterion
        """
        vas        = self._to_float(kwargs.get("dyspnea_vas"))
        rr         = self._to_float(kwargs.get("rr"))
        hr         = self._to_float(kwargs.get("hr"))
        sao2       = self._to_float(kwargs.get("sao2"))
        sao2_delta = self._to_float(kwargs.get("sao2_change"))
        crp        = self._to_float(kwargs.get("crp"))
        paco2      = self._to_float(kwargs.get("paco2"))
        ph         = self._to_float(kwargs.get("ph"))

        # ABG severe criterion
        severe_abg = (paco2 is not None and ph is not None
                      and paco2 > self._PACO2_SEVERE and ph < self._PH_SEVERE)

        abnormal = 0
        assessed = 0

        if vas is not None:
            assessed += 1
            if vas >= self._VAS_MODERATE:
                abnormal += 1

        if rr is not None:
            assessed += 1
            if rr >= self._RR_MODERATE:
                abnormal += 1

        if hr is not None:
            assessed += 1
            if hr >= self._HR_MODERATE:
                abnormal += 1

        # SaO2 and sao2_change together = one parameter
        if sao2 is not None or sao2_delta is not None:
            assessed += 1
            sao2_abnormal = ((sao2 is not None and sao2 < self._SAO2_MODERATE)
                             or (sao2_delta is not None and sao2_delta > self._SAO2_DELTA_MOD))
            if sao2_abnormal:
                abnormal += 1

        if crp is not None:
            assessed += 1
            if crp >= self._CRP_MODERATE:
                abnormal += 1

        return {"abnormal_count": abnormal, "n_assessed": assessed, "severe_abg": severe_abg}

    def classify(self, **kwargs):
        """
        Classify ECOPD severity.

        Returns 'Severe', 'Moderate', 'Mild', or pd.NA when no parameters
        are provided.
        """
        s = self.score(**kwargs)

        if s["n_assessed"] == 0 and not s["severe_abg"]:
            return pd.NA

        if s["severe_abg"]:
            return "Severe"

        if s["abnormal_count"] >= self._MODERATE_THRESHOLD:
            return "Moderate"

        return "Mild"

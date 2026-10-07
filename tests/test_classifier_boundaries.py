"""
Boundary tests for every classifier threshold: just below, at, and just above.

Expected values follow the rule as documented in each classifier's docstring and the
cited source (comparison direction: <, <=, > or >= as stated there). The same
specification (CASES) generates the supplementary boundary table of the manuscript.

Each case: classifier, rule, variable, threshold, base inputs, step, expected
(below, at, above), and the method to call ("classify" or "score"). "Below" and "above"
are threshold -/+ step; integer scales use a step of 1.
"""

import os
import sys
import unittest
import warnings

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pyspiro as ps  # noqa: E402

NA = None   # pd.NA results are compared as None

ERS = "Stanojevic 2022 (z = -1.645 = LLN)"
_OBS_LOWFVC = {"FEV1_z": -3.0, "FVC_z": -2.0, "FEV1FVC_z": -2.0}       # obstruction, FVC < LLN
_RATIO_OK_LOWFVC = {"FEV1_z": -2.0, "FVC_z": -2.0, "FEV1FVC_z": 0.0}   # no obstruction, FVC < LLN
_ROME_TWO = {"dyspnea_vas": 5, "rr": 24, "hr": 90, "sao2": 95, "crp": 5}   # 2 of 5 abnormal
_ROME_NONE = {"dyspnea_vas": 2, "rr": 18, "hr": 80, "sao2": 95, "crp": 5}  # 0 of 5 abnormal


def _bode(points):
    """BODE inputs with a given total score (fev1p, walk6m, mmrc, bmi points)."""
    fev1p = {0: 70, 1: 60, 2: 45, 3: 30}
    walk = {0: 400, 1: 300, 2: 200, 3: 100}
    mmrc = {0: 0, 1: 2, 2: 3, 3: 4}
    f, w, m, b = points
    return {"fev1p": fev1p[f], "walk6m": walk[w], "mmrc": mmrc[m], "bmi": 20 if b else 25}


def _gap(points):
    """GAP inputs with a given total score (sex, age, fvc, dlco points)."""
    s, a, f, d = points
    return {"sex": s, "age": {0: 55, 1: 63, 2: 70}[a], "fvc_pct": {0: 80, 1: 60, 2: 40}[f],
            "dlco_pct": {0: 60, 1: 45, 2: 30}[d]}


# (classifier, rule, variable, threshold, base, step, (below, at, above), method)
CASES = [
    # GOLD 2023: FEV1 % predicted
    ("GOLD", "GOLD 1: FEV1 >= 80 % predicted", "FEV1p", 80.0, {}, 0.01, (2, 1, 1), "classify"),
    ("GOLD", "GOLD 2: 50 <= FEV1 < 80 % predicted", "FEV1p", 50.0, {}, 0.01, (3, 2, 2), "classify"),
    ("GOLD", "GOLD 3: 30 <= FEV1 < 50 % predicted; GOLD 4: < 30", "FEV1p", 30.0, {}, 0.01, (4, 3, 3), "classify"),
    # STAR (Bhatt 2023): FEV1/FVC ratio
    ("STAR", "not staged: FEV1/FVC >= 0.70", "FEV1_FVC", 0.70, {}, 0.0001, (1, NA, NA), "classify"),
    ("STAR", "stage 1: 0.60 <= FEV1/FVC < 0.70", "FEV1_FVC", 0.60, {}, 0.0001, (2, 1, 1), "classify"),
    ("STAR", "stage 2: 0.50 <= FEV1/FVC < 0.60", "FEV1_FVC", 0.50, {}, 0.0001, (3, 2, 2), "classify"),
    ("STAR", "stage 3: 0.40 <= FEV1/FVC < 0.50; stage 4: < 0.40", "FEV1_FVC", 0.40, {}, 0.0001, (4, 3, 3),
     "classify"),
    # ATS/ERS 2022 interpretive pattern (z-scores)
    ("ATS_ERS_2022", "obstruction: FEV1/FVC z < -1.645", "FEV1FVC_z", -1.645,
     {"FEV1_z": 0.0, "FVC_z": 0.0}, 0.001, ("Obstructive", "Normal", "Normal"), "classify"),
    ("ATS_ERS_2022", "obstruction with FVC z < -1.645, TLC not given", "FVC_z", -1.645,
     {"FEV1_z": -3.0, "FEV1FVC_z": -2.0}, 0.001,
     ("Obstructive with reduced FVC", "Obstructive", "Obstructive"), "classify"),
    ("ATS_ERS_2022", "obstruction, FVC low: TLC z < -1.645 -> mixed", "TLC_z", -1.645, _OBS_LOWFVC, 0.001,
     ("Mixed obstructive-restrictive", "Obstructive", "Obstructive"), "classify"),
    ("ATS_ERS_2022", "no obstruction: FVC z < -1.645, TLC not given", "FVC_z", -1.645,
     {"FEV1_z": 0.0, "FEV1FVC_z": 0.0}, 0.001, ("Possible restriction", "Normal", "Normal"), "classify"),
    ("ATS_ERS_2022", "no obstruction, FVC low: TLC z < -1.645 -> restrictive", "TLC_z", -1.645,
     _RATIO_OK_LOWFVC, 0.001, ("Restrictive", ps.ATS_ERS_2022.NSIP, ps.ATS_ERS_2022.NSIP), "classify"),
    ("ATS_ERS_2022", "FEV1/FVC and FVC normal: FEV1 z < -1.645 -> non-specific", "FEV1_z", -1.645,
     {"FVC_z": 0.0, "FEV1FVC_z": 0.0}, 0.001, (ps.ATS_ERS_2022.NSIP, "Normal", "Normal"), "classify"),
    # ERS/ATS 2022 severity (z-score)
    ("LF_SEVERITY_2022", "Normal: z >= -1.645", "z", -1.645, {}, 0.001, ("Mild", "Normal", "Normal"), "classify"),
    ("LF_SEVERITY_2022", "Mild: -2.5 <= z < -1.645", "z", -2.5, {}, 0.001, ("Moderate", "Mild", "Mild"), "classify"),
    ("LF_SEVERITY_2022", "Moderate: -4.0 <= z < -2.5; Severe: z < -4.0", "z", -4.0, {}, 0.001,
     ("Severe", "Moderate", "Moderate"), "classify"),
    ("LF_SEVERITY_2022", "with flag_uln: z > +1.645 -> above ULN", "z", 1.645, {"flag_uln": True}, 0.001,
     ("Normal", "Normal", "Above ULN"), "classify"),
    # BDR 2022: change > 10 % of predicted
    # inputs chosen so that the change is exactly 10.0 % in floating point at the threshold
    ("BDR_2022", "FEV1 change > 10 % of predicted", "post_fev1", 3.5,
     {"pre_fev1": 3.0, "predicted_fev1": 5.0}, 0.001, ("Negative", "Negative", "Positive (FEV1)"), "classify"),
    ("BDR_2022", "FVC change > 10 % of predicted", "post_fvc", 3.5,
     {"pre_fvc": 3.0, "predicted_fvc": 5.0}, 0.001, ("Negative", "Negative", "Positive (FVC)"), "classify"),
    # BODE (Celli 2004): points per variable
    ("BODE", "BMI <= 21 -> 1 point", "bmi", 21.0, {"fev1p": 70, "mmrc": 0, "walk6m": 400}, 0.01, (1, 1, 0), "score"),
    ("BODE", "FEV1 >= 65 % -> 0 points", "fev1p", 65.0, {"bmi": 25, "mmrc": 0, "walk6m": 400}, 0.01, (1, 0, 0),
     "score"),
    ("BODE", "FEV1 50-64 % -> 1 point", "fev1p", 50.0, {"bmi": 25, "mmrc": 0, "walk6m": 400}, 0.01, (2, 1, 1),
     "score"),
    ("BODE", "FEV1 36-49 % -> 2 points; <= 35 -> 3", "fev1p", 36.0, {"bmi": 25, "mmrc": 0, "walk6m": 400}, 0.01,
     (3, 2, 2), "score"),
    ("BODE", "mMRC 0-1 -> 0; 2 -> 1 point", "mmrc", 2, {"bmi": 25, "fev1p": 70, "walk6m": 400}, 1, (0, 1, 2),
     "score"),
    ("BODE", "mMRC 3 -> 2 points; 4 -> 3", "mmrc", 3, {"bmi": 25, "fev1p": 70, "walk6m": 400}, 1, (1, 2, 3),
     "score"),
    ("BODE", "6MWD >= 350 m -> 0 points", "walk6m", 350.0, {"bmi": 25, "fev1p": 70, "mmrc": 0}, 0.1, (1, 0, 0),
     "score"),
    ("BODE", "6MWD 250-349 m -> 1 point", "walk6m", 250.0, {"bmi": 25, "fev1p": 70, "mmrc": 0}, 0.1, (2, 1, 1),
     "score"),
    ("BODE", "6MWD 150-249 m -> 2 points; <= 149 -> 3", "walk6m", 150.0, {"bmi": 25, "fev1p": 70, "mmrc": 0}, 0.1,
     (3, 2, 2), "score"),
    ("BODE", "quartile 1: score 0-2; 2: 3-4", "score", 2, None, 1, (1, 1, 2), "classify"),
    ("BODE", "quartile 2: score 3-4; 3: 5-6", "score", 4, None, 1, (2, 2, 3), "classify"),
    ("BODE", "quartile 3: score 5-6; 4: 7-10", "score", 6, None, 1, (3, 3, 4), "classify"),
    # GAP (Ley 2012): points and stages
    ("GAP", "age <= 60 -> 0 points; 61-65 -> 1", "age", 60, {"sex": 0, "fvc_pct": 80, "dlco_pct": 60}, 1,
     (0, 0, 1), "score"),
    ("GAP", "age 61-65 -> 1 point; > 65 -> 2", "age", 65, {"sex": 0, "fvc_pct": 80, "dlco_pct": 60}, 1,
     (1, 1, 2), "score"),
    ("GAP", "FVC > 75 % -> 0 points", "fvc_pct", 75.0, {"sex": 0, "age": 55, "dlco_pct": 60}, 0.01, (1, 1, 0),
     "score"),
    ("GAP", "FVC 50-75 % -> 1 point; < 50 -> 2", "fvc_pct", 50.0, {"sex": 0, "age": 55, "dlco_pct": 60}, 0.01,
     (2, 1, 1), "score"),
    ("GAP", "DLCO > 55 % -> 0 points", "dlco_pct", 55.0, {"sex": 0, "age": 55, "fvc_pct": 80}, 0.01, (1, 1, 0),
     "score"),
    ("GAP", "DLCO 36-55 % -> 1 point; <= 35 -> 2", "dlco_pct", 35.0, {"sex": 0, "age": 55, "fvc_pct": 80}, 0.01,
     (2, 2, 1), "score"),
    ("GAP", "stage I: score 0-3; II: 4-5", "score", 3, None, 1, ("I", "I", "II"), "classify"),
    ("GAP", "stage II: score 4-5; III: 6-8", "score", 5, None, 1, ("II", "II", "III"), "classify"),
    # GOLD ABE (GOLD 2023)
    ("GOLD_ABE", "E: >= 2 moderate exacerbations", "exac_moderate", 2,
     {"exac_hospitalised": 0, "cat": 5, "mmrc": 0}, 1, ("A", "E", "E"), "classify"),
    ("GOLD_ABE", "E: >= 1 hospitalised exacerbation", "exac_hospitalised", 1,
     {"exac_moderate": 0, "cat": 5, "mmrc": 0}, 1, ("A", "E", "E"), "classify"),
    ("GOLD_ABE", "B: CAT >= 10", "cat", 10, {"exac_moderate": 0, "exac_hospitalised": 0, "mmrc": 0}, 1,
     ("A", "B", "B"), "classify"),
    ("GOLD_ABE", "B: mMRC >= 2", "mmrc", 2, {"exac_moderate": 0, "exac_hospitalised": 0, "cat": 5}, 1,
     ("A", "B", "B"), "classify"),
    # ECOPD Rome 2021: moderate if >= 3 of 5 primary parameters abnormal; severe by ABG
    ("ECOPD_ROME_2021", "dyspnea VAS >= 5 (3rd abnormal parameter)", "dyspnea_vas", 5.0,
     dict(_ROME_TWO, dyspnea_vas=2, hr=95), 0.01, ("Mild", "Moderate", "Moderate"), "classify"),
    ("ECOPD_ROME_2021", "respiratory rate >= 24 (3rd abnormal parameter)", "rr", 24.0,
     dict(_ROME_TWO, rr=18, hr=95), 0.01, ("Mild", "Moderate", "Moderate"), "classify"),
    ("ECOPD_ROME_2021", "heart rate >= 95 (3rd abnormal parameter)", "hr", 95.0, _ROME_TWO, 0.01,
     ("Mild", "Moderate", "Moderate"), "classify"),
    ("ECOPD_ROME_2021", "SaO2 < 92 % (3rd abnormal parameter)", "sao2", 92.0, _ROME_TWO, 0.01,
     ("Moderate", "Mild", "Mild"), "classify"),
    ("ECOPD_ROME_2021", "SaO2 change > 3 % (3rd abnormal parameter)", "sao2_change", 3.0, _ROME_TWO, 0.01,
     ("Mild", "Mild", "Moderate"), "classify"),
    ("ECOPD_ROME_2021", "CRP >= 10 mg/L (3rd abnormal parameter)", "crp", 10.0, _ROME_TWO, 0.01,
     ("Mild", "Moderate", "Moderate"), "classify"),
    ("ECOPD_ROME_2021", "severe: PaCO2 > 45 mmHg (with pH < 7.35)", "paco2", 45.0, dict(_ROME_NONE, ph=7.30), 0.01,
     ("Mild", "Mild", "Severe"), "classify"),
    ("ECOPD_ROME_2021", "severe: pH < 7.35 (with PaCO2 > 45)", "ph", 7.35, dict(_ROME_NONE, paco2=50), 0.001,
     ("Severe", "Mild", "Mild"), "classify"),
    # WODEHOUSE 2003: nNO cut-off
    ("WODEHOUSE_2003", "nNO < 200 ppb -> PCD range", "nno_ppb", 200.0, {}, 0.01, ("PCD range", "Normal", "Normal"),
     "classify"),
    # PCD_SEVERITY (experimental, custom thresholds)
    ("PCD_SEVERITY", "LCI z > 1.645 -> moderate", "lci_zscore", 1.645, {"fev1_zscore": 0.0}, 0.001,
     ("Mild", "Mild", "Moderate"), "classify"),
    ("PCD_SEVERITY", "LCI z > 3.0 -> severe", "lci_zscore", 3.0, {"fev1_zscore": 0.0}, 0.001,
     ("Moderate", "Moderate", "Severe"), "classify"),
    ("PCD_SEVERITY", "FEV1 z < -1.645 -> moderate", "fev1_zscore", -1.645, {"lci_zscore": 0.0}, 0.001,
     ("Moderate", "Mild", "Mild"), "classify"),
    ("PCD_SEVERITY", "FEV1 z < -2.5 -> severe", "fev1_zscore", -2.5, {"lci_zscore": 0.0}, 0.001,
     ("Severe", "Moderate", "Moderate"), "classify"),
    ("PCD_SEVERITY", "nNO >= 200 ppb -> inconclusive", "nno_ppb", 200.0, {"lci_zscore": 0.0, "fev1_zscore": 0.0},
     0.01, ("Mild", "Inconclusive", "Inconclusive"), "classify"),
]

# total score -> inputs that produce it (for the BODE quartile and GAP stage rows)
_BODE_SCORE = {1: (1, 0, 0, 0), 2: (1, 1, 0, 0), 3: (1, 1, 1, 0), 4: (2, 1, 1, 0), 5: (2, 2, 1, 0),
               6: (2, 2, 2, 0), 7: (3, 2, 2, 0)}
_GAP_SCORE = {2: (0, 1, 1, 0), 3: (1, 1, 1, 0), 4: (1, 1, 1, 1), 5: (1, 2, 1, 1), 6: (1, 2, 2, 1)}


def run_case(case):
    """Return [(position, value, inputs, expected, observed)] for below / at / above."""
    clf, _rule, var, thr, base, step, expected, method = case
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)    # PCD_SEVERITY warns on instantiation
        obj = getattr(ps, clf)()
    out = []
    for pos, val, exp in zip(("below", "at", "above"), (thr - step, thr, thr + step), expected):
        if base is None:                            # total-score rows: build inputs for that score
            score = int(round(val))
            inputs = _bode(_BODE_SCORE[score]) if clf == "BODE" else _gap(_GAP_SCORE[score])
        else:
            val = round(val, 10)
            inputs = dict(base, **{var: val})
        got = getattr(obj, method)(**inputs)
        got = None if got is pd.NA else got
        out.append((pos, val, inputs, exp, got))
    return out


class TestClassifierBoundaries(unittest.TestCase):
    def test_every_threshold_below_at_above(self):
        for case in CASES:
            for pos, val, inputs, exp, got in run_case(case):
                with self.subTest(classifier=case[0], rule=case[1], position=pos, value=val):
                    self.assertEqual(got, exp)


if __name__ == "__main__":
    unittest.main()

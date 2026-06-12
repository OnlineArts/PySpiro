import pandas as pd
import pytest

from pyspiro import ECOPD_ROME_2021


@pytest.fixture
def clf():
    return ECOPD_ROME_2021()


# ---------------------------------------------------------------------------
# Severe: ABG criterion (PaCO2 > 45 AND pH < 7.35) — overrides everything
# ---------------------------------------------------------------------------

def test_severe_abg(clf):
    assert clf.classify(paco2=50, ph=7.30) == "Severe"


def test_severe_abg_boundary_paco2_exact(clf):
    # PaCO2 must be > 45 (strictly); exactly 45 mmHg is NOT severe
    result = clf.classify(paco2=45, ph=7.30)
    assert pd.isna(result) or result != "Severe"


def test_severe_abg_boundary_ph_exact(clf):
    # pH must be < 7.35 (strictly); exactly 7.35 is NOT severe
    result = clf.classify(paco2=50, ph=7.35)
    assert pd.isna(result) or result != "Severe"


def test_severe_requires_both_abg_fields(clf):
    # Only paco2 provided → cannot evaluate severe criterion → returns pd.NA
    result = clf.classify(paco2=50)
    assert pd.isna(result)


def test_severe_overrides_mild_primary_params(clf):
    # Even if all primary params are mild, ABG alone → Severe
    assert clf.classify(
        dyspnea_vas=2, rr=18, hr=80, sao2=95, crp=5,
        paco2=50, ph=7.30
    ) == "Severe"


# ---------------------------------------------------------------------------
# Moderate: ≥3 of 5 primary parameters abnormal
# ---------------------------------------------------------------------------

def test_moderate_three_of_five(clf):
    assert clf.classify(
        dyspnea_vas=6,   # abnormal
        rr=26,           # abnormal
        hr=97,           # abnormal
        sao2=95,         # normal
        crp=5,           # normal
    ) == "Moderate"


def test_moderate_exactly_three(clf):
    assert clf.classify(
        dyspnea_vas=5,   # abnormal (boundary)
        rr=24,           # abnormal (boundary)
        hr=95,           # abnormal (boundary)
    ) == "Moderate"


def test_moderate_sao2_and_crp_complete(clf):
    assert clf.classify(
        dyspnea_vas=3,   # normal
        rr=20,           # normal
        hr=80,           # normal
        sao2=89,         # abnormal
        crp=15,          # abnormal
    ) == "Mild"          # only 2 abnormal → Mild


def test_moderate_four_abnormal(clf):
    assert clf.classify(
        dyspnea_vas=7,
        rr=28,
        hr=100,
        sao2=88,
        crp=20,
    ) == "Moderate"


# ---------------------------------------------------------------------------
# SaO2 criterion: one parameter comprising two sub-measures
# ---------------------------------------------------------------------------

def test_sao2_absolute_triggers_moderate_criterion(clf):
    # SaO2 < 92 alone counts
    assert clf.classify(
        dyspnea_vas=6, rr=25, sao2=90
    ) == "Moderate"


def test_sao2_delta_triggers_moderate_criterion(clf):
    # Change > 3% alone counts even if absolute SaO2 is fine
    assert clf.classify(
        dyspnea_vas=6, rr=25, sao2_change=4
    ) == "Moderate"


def test_sao2_neither_abnormal(clf):
    # SaO2 ≥ 92 and no change → SaO2 criterion normal; only VAS+RR abnormal → Mild
    assert clf.classify(dyspnea_vas=6, rr=25, sao2=93) == "Mild"


def test_sao2_and_change_count_as_one(clf):
    # Both sao2 and sao2_change provided but together = 1 parameter
    s = ECOPD_ROME_2021().score(
        dyspnea_vas=6, rr=25, hr=96, sao2=88, sao2_change=5
    )
    assert s["n_assessed"] == 4   # vas + rr + hr + sao2/change (1 combined)


# ---------------------------------------------------------------------------
# Mild: default when <3 parameters are abnormal
# ---------------------------------------------------------------------------

def test_mild_default_all_normal(clf):
    assert clf.classify(
        dyspnea_vas=2, rr=18, hr=80, sao2=96, crp=5
    ) == "Mild"


def test_mild_two_abnormal(clf):
    assert clf.classify(
        dyspnea_vas=6, rr=26, hr=80, sao2=96, crp=5
    ) == "Mild"


def test_mild_no_abg_provided(clf):
    assert clf.classify(dyspnea_vas=2, rr=16) == "Mild"


# ---------------------------------------------------------------------------
# Missing / None inputs
# ---------------------------------------------------------------------------

def test_no_parameters_returns_na(clf):
    assert pd.isna(clf.classify())


def test_crp_missing_does_not_count(clf):
    # 4 parameters assessed; 3 abnormal → still Moderate
    assert clf.classify(
        dyspnea_vas=6, rr=25, hr=96, sao2=88
        # crp omitted
    ) == "Moderate"


def test_partial_inputs_mild(clf):
    # Only 1 abnormal of 2 assessed → Mild
    assert clf.classify(dyspnea_vas=6, rr=18) == "Mild"


# ---------------------------------------------------------------------------
# score() transparency
# ---------------------------------------------------------------------------

def test_score_structure(clf):
    s = clf.score(dyspnea_vas=6, rr=26, hr=80, sao2=96, crp=5)
    assert "abnormal_count" in s
    assert "n_assessed" in s
    assert "severe_abg" in s
    assert s["abnormal_count"] == 2
    assert s["n_assessed"] == 5
    assert s["severe_abg"] is False


def test_score_severe_abg_flag(clf):
    s = clf.score(paco2=48, ph=7.28)
    assert s["severe_abg"] is True


# ---------------------------------------------------------------------------
# get_order()
# ---------------------------------------------------------------------------

def test_get_order(clf):
    assert clf.get_order() == ["Mild", "Moderate", "Severe"]

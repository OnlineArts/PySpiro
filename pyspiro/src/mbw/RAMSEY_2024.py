import math
from enum import Enum

import numpy
import pandas

from ..reference import LMSReference


class RAMSEY_2024(LMSReference):
    """
    GLI Multiple Breath Washout reference equations (Ramsey et al. 2024).

    Provides predicted values, z-scores, LLN, and ULN for:
        LCI   — Lung Clearance Index (dimensionless turnover index)
        FRC   — Functional Residual Capacity (litres)

    Both parameters use the GAMLSS BCCG (Box-Cox Cole and Green) model.
    Predicted M, S, and L are derived from fixed linear terms plus age-dependent
    spline correction terms stored in pre-computed lookup tables extracted from
    the GLI 2024 supplementary material.

    LCI has no sex or height dependence; FRC depends on sex, age, and height.
    Age range: 2–80 years.  Height in cm (relevant only for FRC).

    BCCG z-score formula:
        z = [(x / M)^L − 1] / (L × S)
    LLN (5th percentile, z = −1.645):
        M × (1 − 1.645 × L × S)^(1/L)
    ULN (95th percentile, z = +1.645):
        M × (1 + 1.645 × L × S)^(1/L)

    LCI Table 2 equations:
        M = exp{1.817 + 0.001308 × age + Mspline(age)}
        S = exp{−2.540 − 0.0002242 × age + Sspline(age)}
        L = −0.3964

    FRC Table 2 equations:
        M = exp{intercept + 0.006038 × age + 0.01957 × height + Mspline(age)}
          intercept: −2.468 (male), −2.512 (female)
        S = exp{−1.392 − 0.001590 × height}
        L = 0.6471  (no spline correction)

    Variables: sex (0=female, 1=male), age (years, 2–80), height (cm).
    Parameters: LCI, FRC.
    No ethnicity stratification.

    Citation:
        Ramsey KA, Rosenow T, Turkovic L, … Stick SM, Sly PD,
        Ranganathan S, Robinson PD; Paediatric Respirology International
        Multicentre Study (PRINS) collaboration.
        Global Lung Function Initiative reference equations for
        multiple-breath washout measurements.
        Eur Respir J. 2024;63(1):2400524.
        doi: 10.1183/13993003.00524-2024.
    """

    class Parameters(Enum):
        LCI = 1
        FRC = 2

    _AGE_RANGE = (2.0, 80.0)

    # LCI — Table 2 coefficients
    _LCI_L                 = -0.3964
    _LCI_M_INTERCEPT       =  1.817
    _LCI_M_AGE_COEF        =  0.001308
    _LCI_S_INTERCEPT       = -2.540
    _LCI_S_AGE_COEF        = -0.0002242

    # FRC — Table 2 coefficients
    _FRC_L                   =  0.6471
    _FRC_M_INTERCEPT_MALE    = -2.468
    _FRC_M_INTERCEPT_FEMALE  = -2.512
    _FRC_M_AGE_COEF          =  0.006038
    _FRC_M_HEIGHT_COEF       =  0.01957
    _FRC_S_INTERCEPT         = -1.392
    _FRC_S_HEIGHT_COEF       = -0.001590

    def __init__(self):
        import importlib.resources
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'ramsey_2024_lci_splines.csv').open('rb') as f:
            lci_df = pandas.read_csv(f, delimiter=';')
        with (pkg / 'ramsey_2024_frc_splines.csv').open('rb') as f:
            frc_df = pandas.read_csv(f, delimiter=';')
        self._lci_ages     = lci_df['age'].values
        self._lci_mspline  = lci_df['Mspline'].values
        self._lci_sspline  = lci_df['Sspline'].values
        self._frc_ages     = frc_df['age'].values
        self._frc_mspline  = frc_df['Mspline'].values

    def _interp_lci_splines(self, age: float) -> tuple:
        ms = float(numpy.interp(age, self._lci_ages, self._lci_mspline))
        ss = float(numpy.interp(age, self._lci_ages, self._lci_sspline))
        return ms, ss

    def _interp_frc_mspline(self, age: float) -> float:
        return float(numpy.interp(age, self._frc_ages, self._frc_mspline))

    def lms(self, sex: int, age: float, height: float, parameter: int,
            value: float = None) -> tuple:
        """Return (L, M, S) for the given inputs."""
        age = self.validate_range(float(age), self._AGE_RANGE, 'age')
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        p = self.Parameters(parameter)

        if p == self.Parameters.LCI:
            ms, ss = self._interp_lci_splines(age)
            M = math.exp(self._LCI_M_INTERCEPT + self._LCI_M_AGE_COEF * age + ms)
            S = math.exp(self._LCI_S_INTERCEPT + self._LCI_S_AGE_COEF * age + ss)
            return self._LCI_L, M, S

        if p == self.Parameters.FRC:
            ms = self._interp_frc_mspline(age)
            intercept = (self._FRC_M_INTERCEPT_MALE if sex == self.Sex.MALE.value
                         else self._FRC_M_INTERCEPT_FEMALE)
            M = math.exp(intercept + self._FRC_M_AGE_COEF * age
                         + self._FRC_M_HEIGHT_COEF * float(height) + ms)
            S = math.exp(self._FRC_S_INTERCEPT + self._FRC_S_HEIGHT_COEF * float(height))
            return self._FRC_L, M, S

        return pandas.NA, pandas.NA, pandas.NA

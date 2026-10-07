from ..reference import RegressionReference, RegressionResult
from enum import Enum
import numpy as np
import pandas as pd


class KUSTER_2008(RegressionReference):
    """
    LuftiBus spirometry reference equations (Kuster et al. 2008).

    Reference equations for lung function screening derived from ~8500
    healthy never-smoking adults in the Swiss LuftiBus study. Provides
    predicted values and LLN via separate tabulated equations (no LMS
    framework; ULN is not available from this publication).

    Variables: sex (0=female, 1=male), age (years, 18-80), height (cm).
    Height ranges: males 140-200 cm, females 130-190 cm.
    Parameters: FVC, FEV1, MEF75, MEF50, MEF25, FEV1/FVC%, PEF.
    Use Parameters.*_LLN variants with lln() to obtain the lower limit of normal.

    Citation:
        Kuster SP, Kuster D, Schindler C, et al. Reference equations for lung
        function screening of healthy never-smoking adults aged 18-80 years.
        Eur Respir J. 2008;31(4):860-8.
        doi: 10.1183/09031936.00091407. PMID: 18057057.
    """

    class Parameters(Enum):
        FVC = 1
        FVC_LLN = 2
        FEV1 = 3
        FEV1_LLN = 4
        MEF75 = 5
        MEF75_LLN = 6
        MEF50 = 7
        MEF50_LLN = 8
        MEF25 = 9
        MEF25_LLN = 10
        FEV1_FVC_PCT = 11
        FEV1_FVC_LLN = 12
        PEF = 13
        PEF_LLN = 14

    def __init__(self):
        self._age_range = (18, 80)
        self._height_female_range = (130, 190)
        self._height_male_range = (140, 200)

    # exp(c0 + c1 ln(H) + c2 A + c3 A^2), keyed by (sex, parameter); predicted values (Table 3)
    _PREDICTED_EQUATIONS = {
        (0, Parameters.FVC): (-9.069, 2.013, 0.00847, -0.000155),
        (0, Parameters.FEV1): (-8.397, 1.865, 0.00570, -0.000150),
        (0, Parameters.MEF75): (-2.716, 0.867, 0.00963, -0.000140),
        (0, Parameters.MEF50): (-2.131, 0.674, 0.00895, -0.000180),
        (0, Parameters.MEF25): (-4.861, 1.145, -0.01120, -0.000096),
        (0, Parameters.FEV1_FVC_PCT): (5.637, -0.219, -0.00249, 0.000004),
        (0, Parameters.PEF): (-4.794, 1.316, 0.00926, -0.000143),
        (1, Parameters.FVC): (-10.258, 2.280, 0.00676, -0.000124),
        (1, Parameters.FEV1): (-8.957, 2.014, 0.00281, -0.000105),
        (1, Parameters.MEF75): (-2.227, 0.812, 0.00977, -0.000132),
        (1, Parameters.MEF50): (-3.055, 0.911, 0.00249, -0.000109),
        (1, Parameters.MEF25): (-3.970, 1.009, -0.01645, -0.000020),
        (1, Parameters.FEV1_FVC_PCT): (6.291, -0.341, -0.00441, 0.000026),
        (1, Parameters.PEF): (-3.760, 1.170, 0.00706, -0.000110),
    }

    # exp(c0 + c1 ln(H) + c2 A + c3 A^2), keyed by (sex, parameter); lower limits of normal
    _LLN_EQUATIONS = {
        (0, Parameters.FVC_LLN): (-9.213, 2.013, 0.00616, -0.000155),
        (0, Parameters.FEV1_LLN): (-8.521, 1.865, 0.00357, -0.000150),
        (0, Parameters.MEF75_LLN): (-2.977, 0.867, 0.00698, -0.000140),
        (0, Parameters.MEF50_LLN): (-2.374, 0.674, 0.00330, -0.000180),
        (0, Parameters.MEF25_LLN): (-5.140, 1.145, -0.02002, -0.000096),
        (0, Parameters.FEV1_FVC_LLN): (5.524, -0.219, -0.00313, 0.000004),
        (0, Parameters.PEF_LLN): (-5.032, 1.316, 0.00767, -0.000143),
        (1, Parameters.FVC_LLN): (-10.437, 2.280, 0.00532, -0.000124),
        (1, Parameters.FEV1_LLN): (-9.111, 2.014, 0.00102, -0.000105),
        (1, Parameters.MEF75_LLN): (-2.524, 0.812, 0.00661, -0.000132),
        (1, Parameters.MEF50_LLN): (-3.338, 0.911, -0.00289, -0.000109),
        (1, Parameters.MEF25_LLN): (-4.262, 1.009, -0.02485, -0.000020),
        (1, Parameters.FEV1_FVC_LLN): (6.180, -0.341, -0.00529, 0.000026),
        (1, Parameters.PEF_LLN): (-3.992, 1.170, 0.00493, -0.000110),
    }

    _SCALAR_TYPE = np.float64      # the published equations have always been evaluated with numpy
    _ARRAY_REGRESSION = True

    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        """Not applicable — KUSTER_2008 uses direct polynomial equations, not LMS."""
        return pd.NA, pd.NA, pd.NA

    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Not applicable — KUSTER_2008 does not publish a standard error."""
        return pd.NA

    def _check_conditions(self, sex: int, age, height):
        age, age_na = self._validated(age, self._age_range, "age")
        height_range = self._height_female_range if sex == self.Sex["FEMALE"].value else self._height_male_range
        height, height_na = self._validated(height, height_range, "height")
        if isinstance(age, np.ndarray):
            if sex not in (0, 1):
                for _ in range(len(age)):
                    self.check_tuple(sex, (0, 1), "sex")
            na = age_na | height_na | (sex not in (0, 1))
            return age, height, sex, na
        sex = self.check_tuple(sex, (0, 1), "sex")
        return age, height, sex, age_na or height_na or sex is pd.NA

    @staticmethod
    def _equation(c, age, height):
        return np.exp(c[0] + c[1] * np.log(height) + c[2] * (age) + c[3] * (age ** 2))

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        age, height, sex, na = self._check_conditions(sex, age, height)
        if self._all_na(na):
            return RegressionResult.missing()
        predicted = self._PREDICTED_EQUATIONS.get((sex, parameter))
        lln = self._LLN_EQUATIONS.get((sex, parameter))
        return RegressionResult(
            None if predicted is None else self._equation(predicted, age, height),
            lln=None if lln is None else self._equation(lln, age, height),
            na=na)

    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return % of predicted."""
        r = self._scalar_regression(sex, age, height, ethnicity, None, parameter)
        if r is not None and r.pred is None:
            raise ValueError(f"Unknown parameter for percent calculation: {parameter}")
        return self._percent(r, value)

    def uln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """
        Not implemented — ULN tabulated coefficients are not provided in the KUSTER 2008 publication.
        """
        return pd.NA

    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        r = self._scalar_regression(sex, age, height, ethnicity, None, parameter)
        if r is not None and r.lln is None:
            raise ValueError(f"Unknown parameter for lln calculation: {parameter}")
        return self._lln(r)

    def _check_metric(self, metric, parameter, merged):
        # As percent() and lln(): a parameter without that equation raises unless every row is NA
        field = {'percent': 'pred', 'lln': 'lln'}.get(metric)
        if field is not None and (merged.na_for(field) & ~merged.na).any():
            raise ValueError(f"Unknown parameter for {metric} calculation: {parameter}")

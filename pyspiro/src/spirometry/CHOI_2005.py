from ..reference import RegressionReference, RegressionResult
from enum import Enum
import pandas as pd


class CHOI_2005(RegressionReference):
    """
    Choi et al. (2005) spirometry reference equations for the Korean population.

    Derived from 1,212 healthy non-smoking adults (206 males, 1,006 females) from a
    nationally representative Korean sample (2001–2002), aged 18–70+ years. Mixed-effects
    regression with age², height (cm), and weight (kg) as predictors.

    Parameters: FVC, FEV1, FEV6, FEV1FVC (ratio expressed as %).
    Weight is required for FVC and FEV6; pass weight=None for FEV1 and FEV1FVC.
    No LLN/ULN published; lln(), uln(), and zscore() return pd.NA.

    Citation:
        Choi JK, Paek D, Lee JO. Normal predictive values of spirometry in Korean
        population. Tuberc Respir Dis. 2005;58(3):230–242.
    """

    class Parameters(Enum):
        FVC     = 1
        FEV1    = 2
        FEV6    = 3
        FEV1FVC = 4   # expressed as %

    _AGE_RANGE = (18, 80)
    _age_range = _AGE_RANGE

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param = self.Parameters(parameter)
        m = sex == self.Sex.MALE.value

        age, na = self._validated(age, self._AGE_RANGE, 'age')
        if self._all_na(na):
            return RegressionResult.missing()

        if param == self.Parameters.FVC:
            if weight is None:
                return RegressionResult.missing()
            if m:
                pred = -4.8434 - 0.00008633 * age**2 + 0.05292 * height + 0.01095 * weight
            else:
                pred = -3.0006 - 0.0001273 * age**2 + 0.03951 * height + 0.006892 * weight
        elif param == self.Parameters.FEV1:
            if m:
                pred = -3.4132 - 0.0002484 * age**2 + 0.04578 * height
            else:
                pred = -2.4114 - 0.0001920 * age**2 + 0.03558 * height
        elif param == self.Parameters.FEV6:
            if weight is None:
                return RegressionResult.missing()
            if m:
                pred = -4.4244 - 0.0001367 * age**2 + 0.05156 * height + 0.008246 * weight
            else:
                pred = -3.1433 - 0.0001442 * age**2 + 0.04018 * height + 0.007077 * weight
        elif param == self.Parameters.FEV1FVC:
            if m:
                pred = 119.9004 - 0.3902 * age - 0.1268 * height
            else:
                pred = 97.8567 - 0.2800 * age - 0.01564 * height
        else:
            return RegressionResult.missing()
        return RegressionResult(pred, na=na)

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return self._percent(self._scalar_regression(sex, age, height, ethnicity, weight, parameter), value)

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return pd.NA

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return pd.NA, pd.NA, pd.NA

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return pd.NA

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return pd.NA

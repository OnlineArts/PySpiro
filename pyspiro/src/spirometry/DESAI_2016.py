from ..reference import Reference
from enum import Enum
import math
import pandas as pd


class DESAI_2016(Reference):
    """
    Desai et al. (2016) spirometry prediction equations for adults from Western India.

    Derived from 310 healthy non-smoking adults (185 males, 125 females) at a tertiary
    hospital in Mumbai, aged 18–82 (males) and 18–72 (females), with ethnic origin from
    western India. ATS/ERS 2005 standardisation.

    Log-transformed parameters per sex:
      Males   — LnFVC, LnFEF25_75, LnFEF50, LnFEF75 (FEV1 and PEFR are linear)
      Females — LnFVC, LnFEV1, LnFEF25_75, LnFEF50 (PEFR and FEF75 are linear)
    LLN = predicted − 1.645 × SE  (linear)
        = exp(ln_pred − 1.645 × SE) (log-transformed)

    Weight (kg) is required for: male PEFR, female FEF75.

    Citation:
        Desai U, Joshi JM, Chhabra SK, Rahman M. Prediction equations for spirometry
        in adults in western India. Indian J Tuberc. 2016.
        doi: 10.1016/j.ijtb.2016.08.005.
    """

    class Parameters(Enum):
        FVC      = 1
        FEV1     = 2
        PEFR     = 3
        FEF25_75 = 4   # log-transformed in both sexes
        FEF50    = 5   # log-transformed in both sexes
        FEF75    = 6   # log-transformed in males; linear in females
        FEV1FVC  = 7   # expressed as %

    _AGE_RANGE_MALE   = (18, 82)
    _AGE_RANGE_FEMALE = (18, 72)

    def __init__(self):
        self._age_range = (18, 82)

    def _compute_raw(self, sex: int, age: float, height: float, weight, parameter: int):
        """Return (model_output, SE, is_log_transformed) or (pd.NA, pd.NA, False)."""
        param = self.Parameters(parameter)
        m = sex == self.Sex.MALE.value
        age_range = self._AGE_RANGE_MALE if m else self._AGE_RANGE_FEMALE
        age = self.validate_range(age, age_range, 'age')
        if age is pd.NA:
            return pd.NA, pd.NA, False

        if m:
            if param == self.Parameters.FVC:
                return (-1.048 + 0.015 * height - 0.0045 * age, 0.111, True)
            elif param == self.Parameters.FEV1:
                return (-3.275 + 0.043 * height - 0.020 * age, 0.346, False)
            elif param == self.Parameters.PEFR:
                if weight is None:
                    return pd.NA, pd.NA, False
                return (-1.867 + 0.057 * height - 0.023 * age + 0.024 * weight, 1.08, False)
            elif param == self.Parameters.FEF25_75:
                return (0.044 + 0.009 * height - 0.008 * age, 0.270, True)
            elif param == self.Parameters.FEF50:
                return (-0.033 + 0.010 * height - 0.008 * age, 0.275, True)
            elif param == self.Parameters.FEF75:
                return (-0.246 + 0.0078 * height - 0.020 * age, 0.352, True)
            elif param == self.Parameters.FEV1FVC:
                return (89.09 - 0.179 * age, 4.73, False)
        else:
            if param == self.Parameters.FVC:
                return (-1.616 + 0.015 * height + 0.014 * age - 0.000219 * age**2, 0.097, True)
            elif param == self.Parameters.FEV1:
                return (-1.552 + 0.015 * height + 0.0043 * age - 0.000144 * age**2, 0.115, True)
            elif param == self.Parameters.PEFR:
                return (-1.777 + 0.044 * height + 0.057 * age - 0.000914 * age**2, 0.739, False)
            elif param == self.Parameters.FEF25_75:
                return (-0.270 + 0.012 * height - 0.017 * age, 0.318, True)
            elif param == self.Parameters.FEF50:
                return (-0.299 + 0.009 * height - 0.013 * age, 0.311, True)
            elif param == self.Parameters.FEF75:
                if weight is None:
                    return pd.NA, pd.NA, False
                return (0.273 + 0.019 * height - 0.064 * age - 0.0057 * weight + 0.000448 * age**2, 0.445, False)
            elif param == self.Parameters.FEV1FVC:
                return (104.35 - 0.085 * age + 0.00650 * age**2, 6.34, False)

        return pd.NA, pd.NA, False

    def _predicted(self, sex, age, height, weight, parameter):
        model_out, _, is_log = self._compute_raw(sex, age, height, weight, parameter)
        if model_out is pd.NA:
            return pd.NA
        return math.exp(model_out) if is_log else model_out

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        pred = self._predicted(sex, age, height, weight, parameter)
        return pd.NA if pred is pd.NA else round(value / pred * 100, 2)

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        model_out, se, is_log = self._compute_raw(sex, age, height, weight, parameter)
        if model_out is pd.NA:
            return pd.NA
        if is_log:
            return (math.log(value) - model_out) / se
        return (value - model_out) / se

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return pd.NA, pd.NA, pd.NA

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        model_out, se, is_log = self._compute_raw(sex, age, height, weight, parameter)
        if model_out is pd.NA:
            return pd.NA
        return math.exp(model_out - 1.645 * se) if is_log else model_out - 1.645 * se

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        model_out, se, is_log = self._compute_raw(sex, age, height, weight, parameter)
        if model_out is pd.NA:
            return pd.NA
        return math.exp(model_out + 1.645 * se) if is_log else model_out + 1.645 * se

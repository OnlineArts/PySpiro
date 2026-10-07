from ..reference import RegressionReference, RegressionResult
from enum import Enum
import pandas as pd


class DESAI_2016(RegressionReference):
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

    _age_range = (18, 82)

    def _model(self, m: bool, param, age, height, weight):
        """(model_output, SE, is_log_transformed) of the published equation, or None where it does not apply."""
        if m:
            if param == self.Parameters.FVC:
                return (-1.048 + 0.015 * height - 0.0045 * age, 0.111, True)
            elif param == self.Parameters.FEV1:
                return (-3.275 + 0.043 * height - 0.020 * age, 0.346, False)
            elif param == self.Parameters.PEFR:
                if weight is None:
                    return None
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
                    return None
                return (0.273 + 0.019 * height - 0.064 * age - 0.0057 * weight + 0.000448 * age**2, 0.445, False)
            elif param == self.Parameters.FEV1FVC:
                return (104.35 - 0.085 * age + 0.00650 * age**2, 6.34, False)

        return None

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param = self.Parameters(parameter)
        m = sex == self.Sex.MALE.value
        age, na = self._validated(age, self._AGE_RANGE_MALE if m else self._AGE_RANGE_FEMALE, 'age')
        if self._all_na(na):
            return RegressionResult.missing()

        model = self._model(m, param, age, height, weight)
        if model is None:
            return RegressionResult.missing()
        out, see, is_log = model
        if is_log:
            return RegressionResult(self._exp(out), lln=self._exp(out - 1.645 * see),
                                    uln=self._exp(out + 1.645 * see),
                                    center=out, scale=see, log_z=True, na=na)
        return RegressionResult(out, lln=out - 1.645 * see, uln=out + 1.645 * see,
                                center=out, scale=see, na=na)

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return self._percent(self._scalar_regression(sex, age, height, ethnicity, weight, parameter), value)

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return self._zscore(self._scalar_regression(sex, age, height, ethnicity, weight, parameter), value)

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return pd.NA, pd.NA, pd.NA

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return self._lln(self._scalar_regression(sex, age, height, ethnicity, weight, parameter))

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return self._uln(self._scalar_regression(sex, age, height, ethnicity, weight, parameter))

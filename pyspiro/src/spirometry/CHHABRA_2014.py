from ..reference import RegressionReference, RegressionResult
from enum import Enum
import pandas as pd


class CHHABRA_2014(RegressionReference):
    """
    Chhabra et al. (2014) spirometry prediction equations for adults from Northern India.

    Derived from 685 healthy non-smoking adults (489 males, 196 females) from Delhi and
    the northern Indian states (Punjab, Haryana, Uttar Pradesh), aged 18–71 (males) and
    18–65 (females). ATS/ERS 2005 standardisation.

    Flow rates (PEFR, FEF25_75, FEF50) are log-transformed in both sexes; FEF75 is
    log-transformed in males only. FVC and FEV1 are linear in both sexes.
    LLN = predicted − 1.645 × SEE  (linear parameters)
        = exp(ln_pred − 1.645 × SEE) (log-transformed parameters)

    Weight (kg) is required for: male FVC, male FEF75, male FEV1FVC.

    Citation:
        Chhabra SK, Kumar R, Gupta U, Rahman M, Dash DJ. Prediction equations for
        spirometry in adults from northern India. Indian J Chest Dis Allied Sci.
        2014;56(4):221–229.
    """

    class Parameters(Enum):
        FVC      = 1
        FEV1     = 2
        PEFR     = 3   # log-transformed in both sexes
        FEF25_75 = 4   # log-transformed in both sexes
        FEF50    = 5   # log-transformed in both sexes
        FEF75    = 6   # log-transformed in males; linear in females
        FEV1FVC  = 7   # expressed as %

    _AGE_RANGE_MALE   = (18, 71)
    _AGE_RANGE_FEMALE = (18, 65)

    _age_range = (18, 71)

    def _model(self, m: bool, param, age, height, weight):
        """(model_output, SEE, is_log_transformed) of the published equation, or None where it does not apply."""
        if m:
            if param == self.Parameters.FVC:
                if weight is None:
                    return None
                return (-5.048 - 0.014 * age + 0.054 * height + 0.006 * weight, 0.479, False)
            elif param == self.Parameters.FEV1:
                return (-3.682 - 0.024 * age + 0.046 * height, 0.402, False)
            elif param == self.Parameters.PEFR:
                return (0.346 - 0.004 * age + 0.011 * height, 0.158, True)
            elif param == self.Parameters.FEF25_75:
                return (-0.091 - 0.019 * age + 0.011 * height, 0.271, True)
            elif param == self.Parameters.FEF50:
                return (0.573 - 0.016 * age + 0.008 * height, 0.262, True)
            elif param == self.Parameters.FEF75:
                if weight is None:
                    return None
                return (-0.584 - 0.055 * age + 0.015 * height - 0.005 * weight + 0.000318 * age**2, 0.346, True)
            elif param == self.Parameters.FEV1FVC:
                if weight is None:
                    return None
                return (102.56 - 0.679 * age + 0.00477 * age**2 - 0.080 * weight, 5.79, False)
        else:
            if param == self.Parameters.FVC:
                return (20.07 - 0.010 * age - 0.261 * height + 0.000972 * height**2, 0.315, False)
            elif param == self.Parameters.FEV1:
                return (-2.267 - 0.019 * age + 0.033 * height, 0.286, False)
            elif param == self.Parameters.PEFR:
                return (-0.829 + 0.0137 * height + 0.026 * age - 0.000402 * age**2, 0.198, True)
            elif param == self.Parameters.FEF25_75:
                return (-0.116 + 0.011 * height - 0.0223 * age, 0.308, True)
            elif param == self.Parameters.FEF50:
                return (-0.051 + 0.010 * height - 0.015 * age, 0.292, True)
            elif param == self.Parameters.FEF75:
                return (0.423 - 0.090 * age + 0.000799 * age**2 + 0.017 * height, 0.372, False)
            elif param == self.Parameters.FEV1FVC:
                return (97.182 - 0.440 * age, 4.97, False)

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

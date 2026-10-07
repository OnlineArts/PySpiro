from ..reference import PredictedValueReference, RegressionResult
from enum import Enum
import pandas as pd


class MOKOETLE_1994(PredictedValueReference):
    """
    Mokoetle (1994) spirometry reference equations for black South Africans.

    Mokoetle, KE, de Beer, M, Becklake, MR: A respiratory survey in a black
    Johannesburg workforce. Thorax 1994; 49: 340-346.

    Linear equations using height in cm and age in years for black South African
    adults from Johannesburg. Equations based on standing height (preferred over
    sitting height as they account for more variation).

    Equations derived from 206 men (42.0 ± 10.5 y, 168.7 ± 6.5 cm) and 203 women
    (41.0 ± 9.8 y, 158.0 ± 5.5 cm) working at a Johannesburg university. Study
    population included Sotho, Zulu, Tswana, Venda, Xhosa, and other ethnic groups.

    No LLN published; lln(), uln(), and zscore() return pd.NA.
    FEV1/FVC ratio is not directly provided; can be calculated as FEV1/FVC.

    Citation:
        Mokoetle KE, de Beer M, Becklake MR. A respiratory survey in a black
        Johannesburg workforce. Thorax 1994;49:340-346.
        DOI: 10.1136/thx.49.4.340
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2

    # The paper reports means and SDs, never ranges. Height bounds below are mean ± 2 SD
    # of the study group (Table 4: men 168.7 ± 6.5 cm, women 158.0 ± 5.5 cm). The age
    # bounds follow the paper's age strata, which start at 20 and end at an open '55+'.
    _AGE_RANGE = (20, 65)
    _HEIGHT_MALE_RANGE = (155.7, 181.7)   # cm
    _HEIGHT_FEMALE_RANGE = (147.0, 169.0) # cm

    _age_range = _AGE_RANGE

    def _predicted_fvc_men(self, height: float, age: float) -> float:
        """FVC for men: 0.053 × height - 0.021 × age - 3.85"""
        return 0.053 * height - 0.021 * age - 3.85

    def _predicted_fvc_women(self, height: float, age: float) -> float:
        """FVC for women: 0.045 × height - 0.023 × age - 3.04"""
        return 0.045 * height - 0.023 * age - 3.04

    def _predicted_fev1_men(self, height: float, age: float) -> float:
        """FEV1 for men: 0.035 × height - 0.036 × age - 1.15"""
        return 0.035 * height - 0.036 * age - 1.15

    def _predicted_fev1_women(self, height: float, age: float) -> float:
        """FEV1 for women: 0.034 × height - 0.028 × age - 1.87"""
        return 0.034 * height - 0.028 * age - 1.87

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        age, na = self._validated(age, self._AGE_RANGE, 'age')
        h_range = self._HEIGHT_MALE_RANGE if sex == self.Sex.MALE.value else self._HEIGHT_FEMALE_RANGE
        height, na = self._validated(height, h_range, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        param = self.Parameters(parameter)
        male = sex == self.Sex.MALE.value
        if param == self.Parameters.FVC:
            pred = self._predicted_fvc_men(height, age) if male else self._predicted_fvc_women(height, age)
        elif param == self.Parameters.FEV1:
            pred = self._predicted_fev1_men(height, age) if male else self._predicted_fev1_women(height, age)
        else:
            return RegressionResult.missing()
        return RegressionResult(pred, na=na)

    def _compute(self, sex: int, age: float, height: float, parameter: int) -> float:
        """Compute predicted value for given sex, age, height, and parameter."""
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        return pd.NA if r is None else r.pred

    def percent(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the measured value as % of the predicted median."""
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        if r is None or value is None:
            return pd.NA
        return round((value / r.pred) * 100, 2)

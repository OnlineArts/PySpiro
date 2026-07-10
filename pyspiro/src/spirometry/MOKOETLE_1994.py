from ..reference import Reference
from enum import Enum
import pandas as pd


class MOKOETLE_1994(Reference):
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

    def __init__(self):
        self._age_range = self._AGE_RANGE

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

    def _compute(self, sex: int, age: float, height: float, parameter: int) -> float:
        """Compute predicted value for given sex, age, height, and parameter."""
        # Validate age range
        age = self.validate_range(age, self._AGE_RANGE, 'age')
        if age is pd.NA:
            return pd.NA

        # Validate height range based on sex
        h_range = self._HEIGHT_MALE_RANGE if sex == self.Sex.MALE.value else self._HEIGHT_FEMALE_RANGE
        height = self.validate_range(height, h_range, 'height')
        if height is pd.NA:
            return pd.NA

        param = self.Parameters(parameter)
        
        if param == self.Parameters.FVC:
            if sex == self.Sex.MALE.value:
                return self._predicted_fvc_men(height, age)
            else:  # Female
                return self._predicted_fvc_women(height, age)
        elif param == self.Parameters.FEV1:
            if sex == self.Sex.MALE.value:
                return self._predicted_fev1_men(height, age)
            else:  # Female
                return self._predicted_fev1_women(height, age)
        else:
            return pd.NA

    def percent(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the measured value as % of the predicted median."""
        pred = self._compute(sex, age, height, parameter)
        if pred is pd.NA or value is None:
            return pd.NA
        return round((value / pred) * 100, 2)

    def zscore(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the z-score. Not available for Mokoetle 1994; returns pd.NA."""
        return pd.NA

    def lms(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the (L, M, S) triplet. Not available for Mokoetle 1994; returns pd.NA."""
        return pd.NA, pd.NA, pd.NA

    def lln(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the lower limit of normal. Not available for Mokoetle 1994; returns pd.NA."""
        return pd.NA

    def uln(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the upper limit of normal. Not available for Mokoetle 1994; returns pd.NA."""
        return pd.NA
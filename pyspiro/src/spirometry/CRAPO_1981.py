from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class CRAPO_1981(Reference):
    """
    Crapo (1981) spirometry reference equations.

    Crapo, et al.: Reference Spirometric Values using Techniques and Equipment
    that Meet ATS Recommendations.
    American Review of Respiratory Disease 1981; 123: 659–664.

    Linear equations using height in cm and age in years.
    FEV1/FVC and FEV3/FVC expressed as percentages.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV05 = 2
        FEV1 = 3
        FEV3 = 4
        FEF25_75 = 5
        FEV1FVC = 6     # expressed as %
        FEV3FVC = 7     # expressed as %

    _AGE_MALE_RANGE = (15, 91)
    _AGE_FEMALE_RANGE = (17, 84)
    _HEIGHT_MALE_RANGE = (157.0, 194.0)    # 61.8–76.4 in
    _HEIGHT_FEMALE_RANGE = (146.0, 178.0)  # 57.5–70.1 in

    def __init__(self):
        self._age_range = (15, 91)
        path = importlib.resources.open_binary('pyspiro.data', 'crapo_1981_coefficients.csv')
        df = pd.read_csv(path, delimiter=';')
        df.set_index(['parameter', 'sex'], inplace=True)
        self._coefficients = df

    def _compute(self, sex: int, age: float, height: float, parameter: int):
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age_range = self._AGE_MALE_RANGE if sex == self.Sex.MALE.value else self._AGE_FEMALE_RANGE
        age = self.validate_range(age, age_range, 'age')
        if age is pd.NA:
            return pd.NA

        h_range = self._HEIGHT_MALE_RANGE if sex == self.Sex.MALE.value else self._HEIGHT_FEMALE_RANGE
        height = self.validate_range(height, h_range, 'height')
        if height is pd.NA:
            return pd.NA

        try:
            row = self._coefficients.loc[(param_name, sex_name)]
        except KeyError:
            return pd.NA

        return float(row['a0']) + float(row['a_ht']) * height + float(row['a_age']) * age

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        pred = self._compute(sex, age, height, parameter)
        return pd.NA if pred is pd.NA else round(value / pred * 100, 2)

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA, pd.NA, pd.NA

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA

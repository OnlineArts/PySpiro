from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class ROBERTS_1991(Reference):
    """
    Roberts (1991) spirometry reference equations.

    Roberts, Michael C. et al.: Reference values and prediction equations for
    normal lung function in non-smoking white urban population.
    Thorax 1991; 46: 643–650.

    Linear equations using height in cm and age in years.
    FEV1/FVC expressed as a percentage.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        PEFR = 4
        FEF50 = 5

    _AGE_RANGE = (18, 86)
    _HEIGHT_MALE_RANGE = (161.0, 196.0)    # 63.4–77.2 in
    _HEIGHT_FEMALE_RANGE = (146.0, 177.0)  # 57.5–69.7 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        path = importlib.resources.open_binary('pyspiro.data', 'roberts_1991_coefficients.csv')
        df = pd.read_csv(path, delimiter=';')
        df.set_index(['parameter', 'sex'], inplace=True)
        self._coefficients = df

    def _compute(self, sex: int, age: float, height: float, parameter: int):
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age = self.validate_range(age, self._AGE_RANGE, 'age')
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

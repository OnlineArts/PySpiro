from ..reference import Reference
from enum import Enum
import importlib.resources
import math
import pandas as pd


class QUANJER_1995(Reference):
    """
    Quanjer (1995) spirometry reference equations for children and adolescents.

    Quanjer, PhH, et al.: Spirometric Values for White European Children and
    Adolescents: Polgar Revisited.
    Pediatric Pulmonology 1995; 19: 135–142.

    Formula (FVC, FEV1): predicted = exp(a0 + (b0 + b1 * A) * H[m])
    FEV1/FVC is a sex-specific constant (not dependent on height or age).
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %

    _AGE_RANGE = (6, 18)
    _HEIGHT_MALE_RANGE = (110.0, 205.0)    # 43.3–80.7 in
    _HEIGHT_FEMALE_RANGE = (110.0, 185.0)  # 43.3–72.8 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        path = importlib.resources.open_binary('pyspiro.data', 'quanjer_1995_coefficients.csv')
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

        if row['type'] == 'const':
            return float(row['a0'])

        height_m = height / 100.0
        return math.exp(float(row['a0']) + (float(row['b0']) + float(row['b1']) * age) * height_m)

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

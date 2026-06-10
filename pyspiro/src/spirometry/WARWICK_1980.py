from ..reference import Reference
from enum import Enum
import importlib.resources
import math
import pandas as pd


class WARWICK_1980(Reference):
    """
    Warwick (1977/80) spirometry reference equations for children.

    Warwick, WJ: Pulmonary Function in Healthy Minnesota Children.
    Minnesota Medicine 1977; Supplement 60: 435–440.
    Minnesota Medicine March 1980; 191–195.

    Log-linear equations: ln(predicted) = a * ln(H[cm]) + b,
    so predicted = H[cm]^a * exp(b).

    FEV1/FVC is returned as a percentage (decimal result × 100).
    FET (forced expiratory time) is in seconds.
    Volumes in L; flows in L/sec.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        FEF50 = 4
        FEF75 = 5
        PEFR = 6
        FET = 7         # forced expiratory time in seconds

    _AGE_RANGE = (0, 18)                  # < 18 years
    _HEIGHT_MALE_RANGE = (90.0, 188.0)   # 35.4–74 in
    _HEIGHT_FEMALE_RANGE = (90.0, 178.0) # 35.4–70.1 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        path = importlib.resources.open_binary('pyspiro.data', 'warwick_1980_coefficients.csv')
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

        result = math.exp(float(row['a']) * math.log(height) + float(row['b']))
        if param_name == 'FEV1FVC':
            result *= 100.0
        return result

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

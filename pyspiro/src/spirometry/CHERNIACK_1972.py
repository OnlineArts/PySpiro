from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class CHERNIACK_1972(Reference):
    """
    Cherniack (1972) spirometry reference equations.

    Cherniack, RM and Raber, MB: Normal Standards for Ventilatory Function
    Using an Automatic Wedge Spirometer.
    American Review of Respiratory Disease 1972; Vol 106(1), p38–46.

    Linear equations using height in inches. Input height is expected in cm and
    converted internally. MVV is in L/min; all other flows in L/sec.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF25 = 3
        FEF50 = 4
        FEF75 = 5
        FEF25_75 = 6
        PEFR = 7
        MVV = 8

    _AGE_RANGE = (15, 79)
    _HEIGHT_RANGE = (88.9, 215.9)   # 35–85 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        with (importlib.resources.files('pyspiro.data') / 'cherniack_1972_coefficients.csv').open('rb') as f:
            df = pd.read_csv(f, delimiter=';')
        df.set_index(['parameter', 'sex'], inplace=True)
        self._coefficients = df

    def _compute(self, sex: int, age: float, height: float, parameter: int):
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age = self.validate_range(age, self._AGE_RANGE, 'age')
        if age is pd.NA:
            return pd.NA

        height = self.validate_range(height, self._HEIGHT_RANGE, 'height')
        if height is pd.NA:
            return pd.NA
        height_in = height / 2.54

        try:
            row = self._coefficients.loc[(param_name, sex_name)]
        except KeyError:
            return pd.NA

        return float(row['a0']) + float(row['a_ht']) * height_in + float(row['a_age']) * age

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

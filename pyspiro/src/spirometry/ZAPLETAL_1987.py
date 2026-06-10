from ..reference import Reference
from enum import Enum
import importlib.resources
import math
import pandas as pd


class ZAPLETAL_1987(Reference):
    """
    Zapletal (1987) spirometry reference equations for children and adolescents.

    Zapletal, A.: Lung Function in Children and Adolescents. Methods, Reference
    Values. Progress in Respiration Research Vol 22 (1987).

    Two formula types:
      power10 : predicted = 10^(a + b * log10(H[cm])) / divisor
                (divisor = 1000 converts mL→L or mL/min→L/min for volume params)
      linear  : predicted = a + b * H[cm]  (used for FEV1/FVC%)

    FVC, FEV1, SVC in L; FEF and PEFR in L/sec; MVV in L/min.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        FEF25 = 4
        FEF50 = 5
        FEF75 = 6
        FEF25_75 = 7
        PEFR = 8
        SVC = 9
        MVV = 10

    _AGE_RANGE = (6, 18)
    _HEIGHT_RANGE = (107.0, 182.0)    # 42.1–71.7 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        with (importlib.resources.files('pyspiro.data') / 'zapletal_1987_coefficients.csv').open('rb') as f:
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

        try:
            row = self._coefficients.loc[(param_name, sex_name)]
        except KeyError:
            return pd.NA

        if row['type'] == 'power10':
            return (10 ** (float(row['a']) + float(row['b']) * math.log10(height))) / float(row['divisor'])
        else:
            return float(row['a']) + float(row['b']) * height

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

from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class POLGAR_1971(Reference):
    """
    Polgar (1971) spirometry reference equations for children.

    Polgar and Promadhat: Pulmonary Function Testing in Children:
    Techniques and Standards 1971.

    Two formula types per parameter:
      power  : predicted = coeff_a * H[cm]^coeff_b  (FVC, FEV1 in L)
      linear : predicted = (coeff_a + coeff_b * H[cm]) / divisor
               (FEF25–75% and PEFR given in L/min, divisor=60 converts to L/sec;
                MVV in L/min, divisor=1)

    FEV1/FVC is not directly available; use Pred FEV1 / Pred FVC.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF25_75 = 3    # L/sec
        PEFR = 4        # L/sec
        MVV = 5         # L/min

    _AGE_RANGE = (4, 17)
    _HEIGHT_RANGE = (110.0, 170.0)    # 43.3–67 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        with (importlib.resources.files('pyspiro.data') / 'polgar_1971_coefficients.csv').open('rb') as f:
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

        if row['type'] == 'power':
            return float(row['coeff_a']) * (height ** float(row['coeff_b']))
        else:
            return (float(row['coeff_a']) + float(row['coeff_b']) * height) / float(row['divisor'])

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

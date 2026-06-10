from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class HSU_1979(Reference):
    """
    Hsu (1979) spirometry reference equations for children and young adults.

    Hsu, Katharine, et al.: Ventilatory Functions of Normal Children and Young
    Adults – Mexican American, White and Black.
    J Pediatr 1979; 95: 14–23.

    Power-law equations: predicted = coeff * H[cm]^exp.
    FVC and FEV1 include a 1/1000 scale factor (formula result in mL → L).
    PEFR and FEF25–75% are given in L/min by the paper and converted to L/sec.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        PEFR = 3
        FEF25_75 = 4

    class Ethnicity(Enum):
        CAUCASIAN = 1
        AFRICAN_AMERICAN = 2
        MEXICAN_AMERICAN = 3

    _AGE_MALE_RANGE = (7, 20)
    _AGE_FEMALE_RANGE = (7, 18)
    _HEIGHT_RANGE = (111.0, 190.0)    # 43.7–74.8 in

    def __init__(self):
        self._age_range = (7, 20)
        path = importlib.resources.open_binary('pyspiro.data', 'hsu_1979_coefficients.csv')
        df = pd.read_csv(path, delimiter=';')
        df.set_index(['parameter', 'sex', 'ethnicity'], inplace=True)
        self._coefficients = df

    def _compute(self, sex: int, age: float, height: float, ethnicity: int, parameter: int):
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()
        eth_name = self.Ethnicity(ethnicity).name.lower()

        age_range = self._AGE_MALE_RANGE if sex == self.Sex.MALE.value else self._AGE_FEMALE_RANGE
        age = self.validate_range(age, age_range, 'age')
        if age is pd.NA:
            return pd.NA

        height = self.validate_range(height, self._HEIGHT_RANGE, 'height')
        if height is pd.NA:
            return pd.NA

        try:
            row = self._coefficients.loc[(param_name, sex_name, eth_name)]
        except KeyError:
            return pd.NA

        return float(row['coeff']) * (height ** float(row['exp'])) / float(row['divisor'])

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        pred = self._compute(sex, age, height, ethnicity, parameter)
        return pd.NA if pred is pd.NA else round(value / pred * 100, 2)

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA, pd.NA, pd.NA

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA

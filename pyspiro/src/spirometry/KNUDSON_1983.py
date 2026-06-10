from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class KNUDSON_1983(Reference):
    """
    Knudson (1983) spirometry reference equations.

    Knudson, Ronald J., et al.: Change in the Normal Maximum Expiratory
    Flow-Volume Curve with Growth and Aging.
    American Review of Respiratory Disease 1983; 127(5–6): 725–734.

    Subjects are stratified by sex and age group, each with its own linear
    (and occasionally quadratic) regression on height and age. FEV1/FVC
    expressed as a percentage.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF50 = 3
        FEF75 = 4
        FEF25_75 = 5
        FEV1FVC = 6     # expressed as %

    _AGE_MALE_RANGE = (6, 90)
    _AGE_FEMALE_RANGE = (6, 88)

    # Height ranges are stratum-specific (PDF table p.37)
    _HEIGHT_RANGES = {
        'm_6_11':   (111.8, 154.9),  # 44–61 in
        'm_12_24':  (139.7, 193.0),  # 55–76 in
        'm_25plus': (157.5, 195.6),  # 62–77 in
        'f_6_10':   (106.7, 147.3),  # 42–58 in
        'f_11_19':  (132.1, 182.9),  # 52–72 in
        'f_20_69':  (147.3, 180.3),  # 58–71 in
        'f_70plus': (147.3, 167.6),  # 58–66 in
    }

    def __init__(self):
        self._age_range = (6, 90)
        with (importlib.resources.files('pyspiro.data') / 'knudson_1983_coefficients.csv').open('rb') as f:
            df = pd.read_csv(f, delimiter=';')
        df.set_index(['parameter', 'sex', 'age_group'], inplace=True)
        self._coefficients = df

    def _age_group(self, sex: int, age: float) -> str:
        if sex == self.Sex.MALE.value:
            if age <= 11:
                return 'm_6_11'
            elif age <= 24:
                return 'm_12_24'
            return 'm_25plus'
        else:
            if age <= 10:
                return 'f_6_10'
            elif age <= 19:
                return 'f_11_19'
            elif age <= 69:
                return 'f_20_69'
            return 'f_70plus'

    def _compute(self, sex: int, age: float, height: float, parameter: int):
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age_range = self._AGE_MALE_RANGE if sex == self.Sex.MALE.value else self._AGE_FEMALE_RANGE
        age = self.validate_range(age, age_range, 'age')
        if age is pd.NA:
            return pd.NA

        age_group = self._age_group(sex, age)
        height = self.validate_range(height, self._HEIGHT_RANGES[age_group], 'height')
        if height is pd.NA:
            return pd.NA

        try:
            row = self._coefficients.loc[(param_name, sex_name, age_group)]
        except KeyError:
            return pd.NA

        return (float(row['a0'])
                + float(row['a_ht']) * height
                + float(row['a_age']) * age
                + float(row['a_age2']) * age ** 2)

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

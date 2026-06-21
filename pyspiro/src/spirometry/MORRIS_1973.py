from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class MORRIS_1973(Reference):
    """
    Morris (1971/73) spirometry reference equations.

    Morris, James F., et al.: Spirometric Standards for Healthy Non-smoking Adults.
    American Review of Respiratory Disease 1971; vol 103(1): 57–67.
    Morris, James F., et al.: Normal values for the ratio of one-second forced expiratory
    volume to forced vital capacity. ARRD 1973 Vol 108: 1000–1003.

    Linear equations using height in inches. Input height is expected in cm and
    converted internally. FEV1/FVC is expressed as a percentage.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF25_75 = 3
        FEV1FVC = 4     # expressed as %

    _AGE_RANGE = (20, 90)
    _FEV1FVC_AGE_RANGE = (20, 79)
    _HEIGHT_MALE_RANGE = (147.3, 203.2)    # 58–80 in
    _HEIGHT_FEMALE_RANGE = (142.2, 182.9)  # 56–72 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        with (importlib.resources.files('pyspiro.data') / 'morris_1973_coefficients.csv').open('rb') as f:
            df = pd.read_csv(f, delimiter=';')
        df.set_index(['parameter', 'sex'], inplace=True)
        self._coefficients = df

    def _compute(self, sex: int, age: float, height: float, parameter: int):
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age_range = self._FEV1FVC_AGE_RANGE if param_name == 'FEV1FVC' else self._AGE_RANGE
        age = self.validate_range(age, age_range, 'age')
        if age is pd.NA:
            return pd.NA

        h_range = self._HEIGHT_MALE_RANGE if sex == self.Sex.MALE.value else self._HEIGHT_FEMALE_RANGE
        height = self.validate_range(height, h_range, 'height')
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

from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class ECCS_1993(Reference):
    """
    ECCS/ERS (Quanjer 1993) spirometry reference equations.

    Quanjer, Ph.H., et al.: Lung Volumes and Ventilatory Flows: Official Statement
    of the European Respiratory Society.
    European Respiratory Journal 1992–1993; Supplement 15–16: 5–40.

    Linear equations using height in cm and age in years. FEV1/FVC expressed as
    a percentage. Per the paper's note, for subjects aged 18–25 the predicted
    mean equals that for age 25. For males this applies to FEF75, FEF25_75,
    PEFR, and FIVC; for females it applies to all parameters.
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
        FIVC = 9

    _MALE_AGE_CLAMP_PARAMS = frozenset({'FEF75', 'FEF25_75', 'PEFR', 'FIVC'})
    _FEMALE_AGE_CLAMP_PARAMS = frozenset({
        'FVC', 'FEV1', 'FEV1FVC', 'FEF25', 'FEF50', 'FEF75', 'FEF25_75', 'PEFR', 'FIVC'
    })
    _FEF_AGE_MIN = 25

    _AGE_RANGE = (18, 70)
    _HEIGHT_MALE_RANGE = (155.0, 195.0)    # 61–76.8 in
    _HEIGHT_FEMALE_RANGE = (145.0, 180.0)  # 57.1–70.9 in

    def __init__(self):
        self._age_range = self._AGE_RANGE
        path = importlib.resources.open_binary('pyspiro.data', 'eccs_1993_coefficients.csv')
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

        clamp_params = self._MALE_AGE_CLAMP_PARAMS if sex == self.Sex.MALE.value else self._FEMALE_AGE_CLAMP_PARAMS
        effective_age = max(age, self._FEF_AGE_MIN) if param_name in clamp_params else age

        try:
            row = self._coefficients.loc[(param_name, sex_name)]
        except KeyError:
            return pd.NA

        return float(row['a0']) + float(row['a_ht']) * height + float(row['a_age']) * effective_age

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

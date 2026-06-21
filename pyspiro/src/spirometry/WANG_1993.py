from ..reference import Reference
from enum import Enum
import importlib.resources
import math
import pandas as pd


class WANG_1993(Reference):
    """
    Wang (1993) spirometry reference equations for children and adolescents.

    Wang, Xiaobin, et al.: Pulmonary Function Between 6 and 18 Years of Age.
    Pediatric Pulmonology 1993; 15: 75–88.

    Formula: predicted = exp(alpha + beta * ln(H[m]))
    where alpha and beta are looked up from an age-indexed table (integer age).
    FEV1/FVC is returned as a percentage (decimal result × 100).
    FEF25–75% is not available for ages 6–7.

    Currently only Male White coefficients are implemented (from the casestudy
    reference table). Other subgroups (Male Black, Female White, Female Black)
    should be added to wang_1993_coefficients.csv from the original paper.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        FEF25_75 = 4

    class Ethnicity(Enum):
        CAUCASIAN = 1
        AFRICAN_AMERICAN = 2

    _AGE_MALE_RANGE = (6, 18)
    _AGE_FEMALE_RANGE = (7, 18)

    # Height ranges vary by ethnicity: African-American minimum is 120 cm (PDF p.37)
    _HEIGHT_RANGES = {
        ('male',   'caucasian'):        (110.0, 190.0),  # 43.3–74.8 in
        ('male',   'african_american'): (120.0, 190.0),  # 47.2–74.8 in
        ('female', 'caucasian'):        (110.0, 180.0),  # 43.3–70.9 in
        ('female', 'african_american'): (120.0, 180.0),  # 47.2–70.9 in
    }

    _PARAM_COLS = {
        'FVC':     ('fvc_alpha',     'fvc_beta'),
        'FEV1':    ('fev1_alpha',    'fev1_beta'),
        'FEV1FVC': ('fev1fvc_alpha', 'fev1fvc_beta'),
        'FEF25_75':('fef25_75_alpha','fef25_75_beta'),
    }

    def __init__(self):
        self._age_range = (6, 18)
        with (importlib.resources.files('pyspiro.data') / 'wang_1993_coefficients.csv').open('rb') as f:
            df = pd.read_csv(f, delimiter=';')
        df.set_index(['sex', 'ethnicity', 'age'], inplace=True)
        self._coefficients = df

    def _compute(self, sex: int, age: float, height: float, ethnicity: int, parameter: int):
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()
        eth_name = self.Ethnicity(ethnicity).name.lower()

        age_range = self._AGE_MALE_RANGE if sex == self.Sex.MALE.value else self._AGE_FEMALE_RANGE
        age = self.validate_range(age, age_range, 'age')
        if age is pd.NA:
            return pd.NA

        h_range = self._HEIGHT_RANGES.get((sex_name, eth_name))
        if h_range is None:
            return pd.NA
        height = self.validate_range(height, h_range, 'height')
        if height is pd.NA:
            return pd.NA

        age_int = int(age)
        alpha_col, beta_col = self._PARAM_COLS[param_name]

        try:
            row = self._coefficients.loc[(sex_name, eth_name, age_int)]
        except KeyError:
            return pd.NA

        alpha = row[alpha_col]
        beta = row[beta_col]
        if pd.isna(alpha) or pd.isna(beta):
            return pd.NA

        height_m = height / 100.0
        result = math.exp(float(alpha) + float(beta) * math.log(height_m))
        if param_name == 'FEV1FVC':
            result *= 100.0
        return result

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

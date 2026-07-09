from ..reference import Reference
from enum import Enum
import importlib.resources
import math
import pandas as pd


class PEREIRA_2007(Reference):
    """
    Pereira et al. (2007) spirometry reference equations for White adults in Brazil.

    Derived from 643 healthy never-smoking White Brazilian adults (270 men,
    373 women) living in eight Brazilian cities. Spirometry followed Brazilian
    Thoracic Association recommendations.

    Companion set to PRATA_2018, which covers Black adults in Brazil.

    Volumes (FVC, FEV6, FEV1) and their ratios are linear in height and age;
    flows and flow/FVC ratios are log-transformed. Male FEF50, FEF75, FEF25_75
    and FEF75_85 carry no height term, as published.

    Weight
    ------
    Weight influenced predicted FVC, FEV6 and FEV1 in males but not in females,
    so Table 3 publishes two models for each of those three volumes. Both are
    exposed:
        FVC / FEV6 / FEV1           height + age (both sexes)
        FVC_WT / FEV6_WT / FEV1_WT  height + age + weight (males only)
    The _WT parameters return pd.NA for females and when weight is None.
    All other parameters ignore weight.

    Coefficients are loaded from pyspiro/data/pereira_2007_coefficients.csv:
        kind=linear   predicted = a0 + a_ht*height + a_age*age + a_wt*weight
                      LLN       = predicted − lln
        kind=log      predicted = exp(a0 + a_ht*ln(height) + a_age*ln(age))
                      LLN       = predicted × lln

    LLN is the published 5th percentile of the residuals. No SEE or residual SD
    was published, so zscore(), uln() and lms() return pd.NA.

    Known table defects
    -------------------
    Female FEF50: Table 4 prints an age coefficient of -0.044, which predicts
    ~15.0 L/s at the cohort's mean height and age against a reported mean of
    3.40 L/s. The CSV carries -0.444, reconstructed from the paper's own (intact)
    FEF50_FVC equation, which implies ~3.25 L/s. This DEVIATES FROM THE PUBLISHED
    TABLE and is the only coefficient in either Brazilian module that does.

    Female FEV6: Table 4 prints a 5th residual percentile of 0.53 but a lower
    limit of "P - 0.63". Every other row in the table has the two columns agree.
    The lower-limit column (0.63) is used.

    Citation:
        Pereira CAC, Sato T, Rodrigues SC. New reference values for forced
        spirometry in white adults in Brazil.
        J Bras Pneumol. 2007;33(4):397-406. doi: 10.1590/S1806-37132007000400008
    """

    class Parameters(Enum):
        FVC          = 1
        FEV6         = 2
        FEV1         = 3
        FVC_WT       = 4    # height + age + weight (males only)
        FEV6_WT      = 5    # height + age + weight (males only)
        FEV1_WT      = 6    # height + age + weight (males only)
        FEV1FVC      = 7    # expressed as %
        FEV1FEV6     = 8    # expressed as %
        PEF          = 9
        FEF50        = 10
        FEF75        = 11
        FEF25_75     = 12
        FEF75_85     = 13
        FEF50_FVC    = 14   # expressed as %
        FEF75_FVC    = 15   # expressed as %
        FEF25_75_FVC = 16   # expressed as %
        FEF75_85_FVC = 17   # expressed as %

    _AGE_RANGE_MALE      = (26, 86)
    _AGE_RANGE_FEMALE    = (20, 85)
    _HEIGHT_RANGE_MALE   = (152.0, 192.0)
    _HEIGHT_RANGE_FEMALE = (137.0, 182.0)

    _WEIGHT_PARAMS = ('FVC_WT', 'FEV6_WT', 'FEV1_WT')

    def __init__(self):
        self._age_range = (20, 86)
        with (importlib.resources.files('pyspiro.data') / 'pereira_2007_coefficients.csv').open('rb') as f:
            df = pd.read_csv(f, delimiter=';')
        df.set_index(['parameter', 'sex'], inplace=True)
        self._coefficients = df

    def _compute_raw(self, sex: int, age: float, height: float, weight, parameter: int):
        """Return (predicted, lln, is_log) or (pd.NA, pd.NA, False)."""
        param_name = self.Parameters(parameter).name
        male = sex == self.Sex.MALE.value
        sex_name = self.Sex(sex).name.lower()

        if param_name in self._WEIGHT_PARAMS and weight is None:
            return pd.NA, pd.NA, False

        age = self.validate_range(
            age, self._AGE_RANGE_MALE if male else self._AGE_RANGE_FEMALE, 'age')
        if age is pd.NA:
            return pd.NA, pd.NA, False

        height = self.validate_range(
            height, self._HEIGHT_RANGE_MALE if male else self._HEIGHT_RANGE_FEMALE, 'height')
        if height is pd.NA:
            return pd.NA, pd.NA, False

        # The female half of the CSV carries no _WT rows: weight did not influence
        # predicted volumes in females, so those models were never derived.
        try:
            row = self._coefficients.loc[(param_name, sex_name)]
        except KeyError:
            return pd.NA, pd.NA, False

        a0, a_ht, a_age, a_wt, lln = (
            float(row['a0']), float(row['a_ht']), float(row['a_age']),
            float(row['a_wt']), float(row['lln']))

        if row['kind'] == 'log':
            pred = math.exp(a0 + a_ht * math.log(height) + a_age * math.log(age))
            return pred, pred * lln, True

        pred = a0 + a_ht * height + a_age * age + a_wt * (weight or 0.0)
        return pred, pred - lln, False

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        pred, _, _ = self._compute_raw(sex, age, height, weight, parameter)
        return pd.NA if pred is pd.NA else round(value / pred * 100, 2)

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        _, lln, _ = self._compute_raw(sex, age, height, weight, parameter)
        return lln

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        """Not available — no SEE or residual SD was published."""
        return pd.NA

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        """Not available — no upper limit of normal was published."""
        return pd.NA

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None, weight=None):
        return pd.NA, pd.NA, pd.NA

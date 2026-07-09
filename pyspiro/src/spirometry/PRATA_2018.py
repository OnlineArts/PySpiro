from ..reference import Reference
from enum import Enum
import importlib.resources
import math
import pandas as pd


class PRATA_2018(Reference):
    """
    Prata et al. (2018) spirometry reference equations for Black adults in Brazil.

    Derived from 244 healthy never-smoking Black Brazilian adults (120 men,
    124 women) from eight Brazilian cities, with BMI 18-30 kg/m2. Spirometry
    followed Brazilian Thoracic Association and ATS/ERS standards.

    Companion set to PEREIRA_2007 (White adults in Brazil). The authors' finding
    is that predicted FVC and FEV1 are significantly lower in Black than in White
    Brazilian adults, so the two populations require separate equations.

    FVC, FEV1, FEV1/FVC and PEF are linear in height and age. The expiratory
    flows (FEF25_75, FEF50, FEF75) are log-transformed and — as published —
    depend on age alone, carrying no height term. Female PEF likewise carries no
    height term. Weight is not used: "Weight played no relevant role in any of
    the reference equations."

    Coefficients are loaded from pyspiro/data/prata_2018_coefficients.csv:
        kind=linear   predicted = a0 + a_ht*height + a_age*age
                      LLN       = predicted − lln
        kind=log      predicted = exp(a0 + a_ht*ln(height) + a_age*ln(age))
                      LLN       = predicted × lln

    LLN is the published 5th percentile of the residuals. No SEE or residual SD
    was published, so zscore(), uln() and lms() return pd.NA.

    Note on FEV1FVC LLN: the CSV carries the 5th residual percentiles printed in
    Tables 3 and 4 (8.70 male, 7.8 female). The Results text instead rounds these
    to 9 and 8, citing external references. The table values are used so that
    every LLN in this module is derived the same way.

    Citation:
        Prata TA, Mancuzo E, Pereira CAC, Spindola de Miranda S, Sadigursky LV,
        Hirotsu C, Tufik S. Spirometry reference values for Black adults in Brazil.
        J Bras Pneumol. 2018;44(6):449-455. doi: 10.1590/S1806-37562018000000082
    """

    class Parameters(Enum):
        FVC      = 1
        FEV1     = 2
        FEV1FVC  = 3   # expressed as %
        PEF      = 4
        FEF25_75 = 5   # log-transformed, age only
        FEF50    = 6   # log-transformed, age only
        FEF75    = 7   # log-transformed, age only

    _AGE_RANGE_MALE      = (26, 82)
    _AGE_RANGE_FEMALE    = (20, 83)
    _HEIGHT_RANGE_MALE   = (151.0, 187.0)
    _HEIGHT_RANGE_FEMALE = (145.0, 175.0)

    def __init__(self):
        self._age_range = (20, 83)
        with (importlib.resources.files('pyspiro.data') / 'prata_2018_coefficients.csv').open('rb') as f:
            df = pd.read_csv(f, delimiter=';')
        df.set_index(['parameter', 'sex'], inplace=True)
        self._coefficients = df

    def _compute_raw(self, sex: int, age: float, height: float, parameter: int):
        """Return (predicted, lln, is_log) or (pd.NA, pd.NA, False)."""
        param_name = self.Parameters(parameter).name
        male = sex == self.Sex.MALE.value
        sex_name = self.Sex(sex).name.lower()

        age = self.validate_range(
            age, self._AGE_RANGE_MALE if male else self._AGE_RANGE_FEMALE, 'age')
        if age is pd.NA:
            return pd.NA, pd.NA, False

        height = self.validate_range(
            height, self._HEIGHT_RANGE_MALE if male else self._HEIGHT_RANGE_FEMALE, 'height')
        if height is pd.NA:
            return pd.NA, pd.NA, False

        try:
            row = self._coefficients.loc[(param_name, sex_name)]
        except KeyError:
            return pd.NA, pd.NA, False

        a0, a_ht, a_age, lln = (
            float(row['a0']), float(row['a_ht']), float(row['a_age']), float(row['lln']))

        if row['kind'] == 'log':
            pred = math.exp(a0 + a_ht * math.log(height) + a_age * math.log(age))
            return pred, pred * lln, True

        pred = a0 + a_ht * height + a_age * age
        return pred, pred - lln, False

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        pred, _, _ = self._compute_raw(sex, age, height, parameter)
        return pd.NA if pred is pd.NA else round(value / pred * 100, 2)

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        _, lln, _ = self._compute_raw(sex, age, height, parameter)
        return lln

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not available — no SEE or residual SD was published."""
        return pd.NA

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not available — no upper limit of normal was published."""
        return pd.NA

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA, pd.NA, pd.NA

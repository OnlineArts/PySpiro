from ..reference import RegressionReference, RegressionResult
from enum import Enum
import pandas as pd


class PRATA_2018(RegressionReference):
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

    _age_range = (20, 83)
    _coeffs_csv = 'prata_2018_coefficients.csv'

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        male = sex == self.Sex.MALE.value
        sex_name = self.Sex(sex).name.lower()

        age, na = self._validated(
            age, self._AGE_RANGE_MALE if male else self._AGE_RANGE_FEMALE, 'age')
        height, na = self._validated(
            height, self._HEIGHT_RANGE_MALE if male else self._HEIGHT_RANGE_FEMALE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        a0, a_ht, a_age, lln = (
            float(row['a0']), float(row['a_ht']), float(row['a_age']), float(row['lln']))
        if row['kind'] == 'log':
            pred = self._exp(a0 + a_ht * self._log(height) + a_age * self._log(age))
            return RegressionResult(pred, lln=pred * lln, na=na)
        pred = a0 + a_ht * height + a_age * age
        return RegressionResult(pred, lln=pred - lln, na=na)

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return self._percent(self._scalar_regression(sex, age, height, ethnicity, None, parameter), value)

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return self._lln(self._scalar_regression(sex, age, height, ethnicity, None, parameter))

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not available — no SEE or residual SD was published."""
        return pd.NA

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not available — no upper limit of normal was published."""
        return pd.NA

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        return pd.NA, pd.NA, pd.NA

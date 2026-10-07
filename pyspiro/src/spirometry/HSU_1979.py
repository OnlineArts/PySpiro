from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class HSU_1979(PredictedValueReference):
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

    _age_range = (7, 20)
    _coeffs_csv = 'hsu_1979_coefficients.csv'
    _coeffs_index = ('parameter', 'sex', 'ethnicity')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()
        eth_name = self.Ethnicity(ethnicity).name.lower()

        age_range = self._AGE_MALE_RANGE if sex == self.Sex.MALE.value else self._AGE_FEMALE_RANGE
        age, na = self._validated(age, age_range, 'age')
        height, na = self._validated(height, self._HEIGHT_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        row = self._row((param_name, sex_name, eth_name))
        if row is None:
            return RegressionResult.missing()

        return RegressionResult(float(row['coeff']) * (height ** float(row['exp'])) / float(row['divisor']), na=na)

from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class WARWICK_1980(PredictedValueReference):
    """
    Warwick (1977/80) spirometry reference equations for children.

    Warwick, WJ: Pulmonary Function in Healthy Minnesota Children.
    Minnesota Medicine 1977; Supplement 60: 435–440.
    Minnesota Medicine March 1980; 191–195.

    Log-linear equations: ln(predicted) = a * ln(H[cm]) + b,
    so predicted = H[cm]^a * exp(b).

    FEV1/FVC is returned as a percentage (decimal result × 100).
    FET (forced expiratory time) is in seconds.
    Volumes in L; flows in L/sec.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        FEF50 = 4
        FEF75 = 5
        PEFR = 6
        FET = 7         # forced expiratory time in seconds

    _AGE_RANGE = (0, 18)                  # 0-18 years inclusive
    _HEIGHT_MALE_RANGE = (90.0, 188.0)   # 35.4–74 in
    _HEIGHT_FEMALE_RANGE = (90.0, 178.0) # 35.4–70.1 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'warwick_1980_coefficients.csv'
    _coeffs_index = ('parameter', 'sex')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age, na = self._validated(age, self._AGE_RANGE, 'age')
        h_range = self._HEIGHT_MALE_RANGE if sex == self.Sex.MALE.value else self._HEIGHT_FEMALE_RANGE
        height, na = self._validated(height, h_range, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        result = self._exp(float(row['a']) * self._log(height) + float(row['b']))
        if param_name == 'FEV1FVC':
            result *= 100.0
        return RegressionResult(result, na=na)

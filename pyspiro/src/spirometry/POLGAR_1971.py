from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class POLGAR_1971(PredictedValueReference):
    """
    Polgar (1971) spirometry reference equations for children.

    Polgar and Promadhat: Pulmonary Function Testing in Children:
    Techniques and Standards 1971.

    Two formula types per parameter:
      power  : predicted = coeff_a * H[cm]^coeff_b  (FVC, FEV1 in L)
      linear : predicted = (coeff_a + coeff_b * H[cm]) / divisor
               (FEF25–75% and PEFR given in L/min, divisor=60 converts to L/sec;
                MVV in L/min, divisor=1)

    FEV1/FVC is not directly available; use Pred FEV1 / Pred FVC.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF25_75 = 3    # L/sec
        PEFR = 4        # L/sec
        MVV = 5         # L/min

    _AGE_RANGE = (4, 17)
    _HEIGHT_RANGE = (110.0, 170.0)    # 43.3–67 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'polgar_1971_coefficients.csv'
    _coeffs_index = ('parameter', 'sex')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age, na = self._validated(age, self._AGE_RANGE, 'age')
        height, na = self._validated(height, self._HEIGHT_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        if row['type'] == 'power':
            return RegressionResult(float(row['coeff_a']) * (height ** float(row['coeff_b'])), na=na)
        else:
            return RegressionResult((float(row['coeff_a']) + float(row['coeff_b']) * height) / float(row['divisor']), na=na)

from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class QUANJER_1995(PredictedValueReference):
    """
    Quanjer (1995) spirometry reference equations for children and adolescents.

    Quanjer, PhH, et al.: Spirometric Values for White European Children and
    Adolescents: Polgar Revisited.
    Pediatric Pulmonology 1995; 19: 135–142.

    Formula (FVC, FEV1): predicted = exp(a0 + (b0 + b1 * A) * H[m])
    FEV1/FVC is a sex-specific constant (not dependent on height or age).
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %

    _AGE_RANGE = (6, 18)
    _HEIGHT_MALE_RANGE = (110.0, 205.0)    # 43.3–80.7 in
    _HEIGHT_FEMALE_RANGE = (110.0, 185.0)  # 43.3–72.8 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'quanjer_1995_coefficients.csv'
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

        if row['type'] == 'const':
            return RegressionResult(float(row['a0']), na=na)

        height_m = height / 100.0
        return RegressionResult(self._exp(float(row['a0']) + (float(row['b0']) + float(row['b1']) * age) * height_m), na=na)

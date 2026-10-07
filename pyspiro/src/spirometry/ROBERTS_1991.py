from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class ROBERTS_1991(PredictedValueReference):
    """
    Roberts (1991) spirometry reference equations.

    Roberts, Michael C. et al.: Reference values and prediction equations for
    normal lung function in non-smoking white urban population.
    Thorax 1991; 46: 643–650.

    Linear equations using height in cm and age in years.
    FEV1/FVC expressed as a percentage.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        PEFR = 4
        FEF50 = 5

    _AGE_RANGE = (18, 86)
    _HEIGHT_MALE_RANGE = (161.0, 196.0)    # 63.4–77.2 in
    _HEIGHT_FEMALE_RANGE = (146.0, 177.0)  # 57.5–69.7 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'roberts_1991_coefficients.csv'
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

        return RegressionResult(float(row['a0']) + float(row['a_ht']) * height + float(row['a_age']) * age, na=na)

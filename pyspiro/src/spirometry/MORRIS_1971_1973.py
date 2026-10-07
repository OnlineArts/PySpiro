from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class MORRIS_1971_1973(PredictedValueReference):
    """
    Morris (1971/73) spirometry reference equations.

    Morris, James F., et al.: Spirometric Standards for Healthy Non-smoking Adults.
    American Review of Respiratory Disease 1971; vol 103(1): 57–67.
    Morris, James F., et al.: Normal values for the ratio of one-second forced expiratory
    volume to forced vital capacity. ARRD 1973 Vol 108: 1000–1003.

    Linear equations using height in inches. Input height is expected in cm and
    converted internally. FEV1/FVC is expressed as a percentage.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF25_75 = 3
        FEV1FVC = 4     # expressed as %

    _AGE_RANGE = (20, 90)
    _FEV1FVC_AGE_RANGE = (20, 79)
    _HEIGHT_MALE_RANGE = (147.3, 203.2)    # 58–80 in
    _HEIGHT_FEMALE_RANGE = (142.2, 182.9)  # 56–72 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'morris_1971_1973_coefficients.csv'
    _coeffs_index = ('parameter', 'sex')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age_range = self._FEV1FVC_AGE_RANGE if param_name == 'FEV1FVC' else self._AGE_RANGE
        age, na = self._validated(age, age_range, 'age')
        h_range = self._HEIGHT_MALE_RANGE if sex == self.Sex.MALE.value else self._HEIGHT_FEMALE_RANGE
        height, na = self._validated(height, h_range, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        height_in = height / 2.54
        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        return RegressionResult(float(row['a0']) + float(row['a_ht']) * height_in + float(row['a_age']) * age, na=na)
